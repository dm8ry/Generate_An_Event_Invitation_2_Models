# Event Invitation Generator with Dual AI Models 🎉

A sophisticated Python application that generates professional event invitations using AWS Bedrock's Claude AI model. This advanced version implements two AI models for enhanced content generation and customization.

## 🌟 Overview

Event Invitation Generator is a powerful tool that automates the creation of compelling event invitations. By leveraging AWS Bedrock's capabilities and implementing dual AI models, it provides more accurate, context-aware, and professionally crafted invitations for various event types.

## ✨ Key Features

- **Dual AI Model Architecture**
  - Primary model for content generation
  - Secondary model for content refinement and optimization
- **Advanced Content Generation**
  - Context-aware invitation text
  - Smart formatting suggestions
  - Tone and style customization
- **Flexible Configuration**
  - Customizable templates
  - Multiple output formats
  - Personalization options
- **AWS Integration**
  - Seamless AWS Bedrock integration
  - Efficient API utilization
  - Secure credential management

## 🛠️ Technical Stack

- **Backend**
  - Python 3.x
  - AWS SDK (Boto3)
  - AWS Bedrock
- **AI Models**
  - Claude AI (Primary)
  - Secondary AI Model for Enhancement
- **Dependencies**
  - AWS Bedrock SDK
  - Python standard libraries
  - Additional requirements specified in `requirements.txt`

## 🚀 Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/dm8ry/Generate_An_Event_Invitation_2_Models.git
   cd Generate_An_Event_Invitation_2_Models
   ```

2. **Set Up Environment**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS**
   ```bash
   aws configure
   ```
   Enter your AWS credentials when prompted:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region
   - Output format

## 💻 Usage

### Basic Command
```bash
python Generate_An_Event_Invitation.py \
  --event_url <event_url> \
  --generate_email \
  --email_to <recipient_email> \
  --output <output_file> \
  --registration_link <registration_url>
```

### Example
```bash
python Generate_An_Event_Invitation.py \
  --event_url https://aws-experience.com/emea/uki/e/804cf/aws-marketplace---digital-procurement-event \
  --generate_email \
  --email_to your.name@company.com \
  --output invite.txt \
  --registration_link https://aws-experience.com/emea/uki/e/804cf/aws-marketplace---digital-procurement-event
```

## ⚙️ Configuration Options

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--event_url` | URL of the event page | Yes |
| `--generate_email` | Flag to generate email format | No |
| `--email_to` | Recipient email address | If `--generate_email` is used |
| `--output` | Output file path | Yes |
| `--registration_link` | Event registration URL | Yes |

## 🔒 Security

- Ensure AWS credentials are properly configured
- Never commit sensitive credentials to the repository
- Use environment variables for sensitive information
- Follow AWS security best practices

---

