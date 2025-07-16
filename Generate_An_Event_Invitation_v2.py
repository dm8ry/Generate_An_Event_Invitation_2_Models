import asyncio
from playwright.async_api import async_playwright
import boto3
import json
import argparse
import re
import subprocess
import tempfile
import os
import html
from botocore.exceptions import ClientError

# ---------- Step 1: Fetch content using Playwright ----------

async def fetch_page_content(url: str, output_file: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(5000)
        content = await page.text_content("body")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        await browser.close()
    return content

# ---------- Step 2: Generate Invitation using us.amazon.nova-premier-v1:0 (Bedrock) ----------

def generate_invitation_with_bedrock(prompt: str) -> str:
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    # Load model_id from config file
    config_path = os.path.join(os.path.dirname(__file__), "bedrock_config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            model_id = config.get("model_id")
            if not model_id:
                raise ValueError("model_id not found in config file.")
    except Exception as e:
        print(f"❌ Error loading model_id from config: {e}")
        exit(1)

    full_prompt = (
        "You are an expert tech event copywriter.\n"
        "Your task is to generate a compelling, structured invitation from the raw event description below.\n\n"
        "Your output MUST include:\n"
        "- A bold, engaging title and intro (this will be used as the subject)\n"
        "- A clearly marked section for each of the following:\n"
        "  📅 Date\n"
        "  🕘 Time\n"
        "  📍 Location\n"
        "  🗣️ Language\n"
        "  🎯 Who should attend\n"
        "- A high-level agenda\n"
        "- Speaker highlights\n"
        "- Value of attending\n\n"
        "Do not use HTML. Use plain text with markdown-style formatting and spacing for readability.\n\n"
        "Format nicely, with emojis for visual appeal.\n\n"
        "Don't break lines unnecessarily.\n\n"
        "Output format similar to ChatGPT.\n\n"
        f"Raw event description:\n{prompt}"
    )

    request_payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }

    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_payload),
            contentType="application/json",
            accept="application/json",
        )
    except ClientError as e:
        print(f"❌ Bedrock API Error: {e.response['Error']['Message']}")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        exit(1)

    response_body = json.loads(response["body"].read())
    # Debug: print the raw response to help identify the correct field
    print("Bedrock raw response:", response_body)
    # Try extracting the generated text from the actual response structure
    if "output" in response_body:
        output = response_body["output"]
        if (
            isinstance(output, dict)
            and "message" in output
            and "content" in output["message"]
            and isinstance(output["message"]["content"], list)
            and len(output["message"]["content"]) > 0
            and "text" in output["message"]["content"][0]
        ):
            return output["message"]["content"][0]["text"].strip()
    # Fallback: try other possible keys
    if "content" in response_body:
        content = response_body["content"]
        if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
            return content[0]["text"].strip()
        elif isinstance(content, str):
            return content.strip()
    if "result" in response_body:
        return response_body["result"].strip()
    # If nothing found, return empty string
    return ""

# ---------- Step 3: Extract registration link ----------

def extract_registration_link(text: str) -> str:
    match = re.search(r'https?://[^\s"]*register[^\s"]*', text, re.IGNORECASE)
    return match.group(0) if match else ""

# ---------- Step 4: Convert plain text invitation to HTML ----------

def convert_to_html(text: str) -> str:
    lines = text.splitlines()
    html_parts = ['<html><body style="font-family: Arial, sans-serif; font-size: 14px;">']

    for line in lines:
        line = html.escape(line)

        # Convert Markdown-style links [text](url) to HTML links
        line = re.sub(
            r'\[([^\]]+)\]\((https?://[^\)]+)\)',
            r'<a href="\2">\1</a>',
            line
        )

        if line.strip() == "":
            html_parts.append("<br>")
        elif line.strip().startswith("- "):
            html_parts.append(f"<li>{line.strip()[2:]}</li>")
        elif line.startswith("**") and line.endswith("**"):
            html_parts.append(f"<h2>{line.strip('* ')}</h2>")
        elif line.startswith("## "):
            html_parts.append(f"<h3>{line[3:].strip()}</h3>")
        elif line.startswith("### "):
            html_parts.append(f"<h4>{line[4:].strip()}</h4>")
        else:
            html_parts.append(f"<p>{line}</p>")

    html_parts.append("</body></html>")
    return "\n".join(html_parts)

# ---------- Step 5: Create Outlook draft (macOS) using HTML ----------

def create_outlook_draft_mac(subject: str, html_body: str, to: str = ""):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as tmp:
        tmp.write(html_body)
        tmp_path = tmp.name

    script = f'''
    set htmlFile to POSIX file "{tmp_path}" as alias
    set htmlContent to read htmlFile as «class utf8»

    tell application "Microsoft Outlook"
        set newMessage to make new outgoing message with properties {{subject:"{subject}"}}
        tell newMessage
            set content to htmlContent
            if "{to}" is not "" then
                make new recipient at newMessage with properties {{email address:{{address:"{to}"}}}}
            end if
            open
        end tell
        activate
    end tell
    '''

    try:
        subprocess.run(["osascript", "-e", script], check=True)
        print("📧 Draft created in Microsoft Outlook (HTML).")
    except subprocess.CalledProcessError as e:
        print("❌ Failed to create draft:", e)
    finally:
        os.remove(tmp_path)

# ---------- Step 6: Orchestration ----------

def main():
    parser = argparse.ArgumentParser(description="Fetch → Generate → Format → Draft Email (macOS only)")
    parser.add_argument("url", help="Event page URL")
    parser.add_argument("--temp_file", default="input_file.txt")
    parser.add_argument("--output", default=None)
    parser.add_argument("--registration_link", default=None)
    parser.add_argument("--generate_email", action="store_true")
    parser.add_argument("--email_to", default="your.name@company.com")

    args = parser.parse_args()

    print(f"📥 Fetching content from: {args.url}")
    raw_page_content = asyncio.run(fetch_page_content(args.url, args.temp_file))

    with open(args.temp_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("🧠 Generating invitation ...")
    invitation = generate_invitation_with_bedrock(raw_text)

    reg_link = args.registration_link or extract_registration_link(raw_page_content)
    if reg_link:
        markdown_link = f"[Register here]({reg_link})"
        if markdown_link not in invitation:
            invitation += f"\n\n🔗 {markdown_link}"
            print(f"🔗 Registration link added: {reg_link}")
        else:
            print(f"🔗 Registration link already included by the model.")
    else:
        print("⚠️ No registration link found or provided.")

    print("\n✅ --- Generated Invitation ---\n")
    print(invitation)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(invitation)
        print(f"\n📄 Invitation saved to: {args.output}")

    if args.generate_email:
        # Find first bold title line for subject, fallback to generic subject
        subject_line = next((line.strip("* ") for line in invitation.splitlines() if line.startswith("**")), "You're Invited: AWS Tech Event")
        html_body = convert_to_html(invitation)
        create_outlook_draft_mac(subject_line, html_body, to=args.email_to)

if __name__ == "__main__":
    main()
