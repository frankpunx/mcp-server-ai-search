# Contoso IT Support - Frequently Asked Questions

## Account & Access

### Q: How do I reset my password?

**A:** You can reset your password using one of these methods:

1. **Self-service (recommended)**:
   - Go to https://password.contoso.com
   - Click "Forgot Password"
   - Enter your email address
   - Follow the instructions sent to your email

2. **IT Help Desk**:
   - Call x5555 or email helpdesk@contoso.com
   - Provide your employee ID for verification
   - A temporary password will be issued

**Note**: Passwords must be at least 12 characters and include uppercase, lowercase, numbers, and symbols. Passwords expire every 90 days.

---

### Q: How do I set up Multi-Factor Authentication (MFA)?

**A:** MFA is required for all employees. To set up:

1. Download Microsoft Authenticator on your phone
2. Log into https://portal.contoso.com
3. Go to **Security > Multi-Factor Authentication**
4. Click "Add Method" and select "Authenticator App"
5. Scan the QR code with the Authenticator app
6. Enter the 6-digit code to verify

**Backup options**: You can also add a phone number for SMS codes as a backup method.

---

### Q: I'm locked out of my account. What do I do?

**A:** Account lockouts occur after 5 failed login attempts. 

- **Wait 30 minutes**: Accounts automatically unlock after 30 minutes
- **Contact IT**: Call x5555 for immediate unlock
- **Self-unlock**: Use https://unlock.contoso.com with your security questions

---

### Q: How do I request access to a new application or system?

**A:** Submit an access request through the IT Service Portal:

1. Go to https://itportal.contoso.com
2. Click "Request Access"
3. Search for the application
4. Fill out the business justification
5. Submit for manager approval

Typical processing time: 2-3 business days after approval.

---

## VPN & Remote Access

### Q: How do I connect to the company VPN?

**A:** Use the GlobalProtect VPN client:

1. **Download**: GlobalProtect is pre-installed on company laptops. For personal devices, download from https://vpn.contoso.com
2. **Connect**:
   - Open GlobalProtect
   - Enter portal address: `vpn.contoso.com`
   - Sign in with your Contoso credentials
   - Complete MFA verification
3. **Verify**: The icon will turn green when connected

**Troubleshooting**:
- Ensure you're not already on the corporate network
- Try disconnecting and reconnecting
- Restart the GlobalProtect service
- Contact IT if issues persist

---

### Q: Can I use the VPN on my personal device?

**A:** Yes, with restrictions:

- Personal devices must have antivirus software installed
- You must agree to the BYOD policy
- Only web-based applications are accessible
- File share access is not permitted from personal devices

To register a personal device, go to **IT Portal > BYOD Registration**.

---

### Q: The VPN is slow. How can I improve performance?

**A:** Try these steps:

1. Connect to the nearest VPN gateway (auto-selected by default)
2. Disconnect from video calls before large file transfers
3. Use OneDrive instead of mapped network drives
4. Avoid peak hours (9-11 AM) for large downloads
5. Check your home internet speed at speedtest.net

Minimum recommended: 25 Mbps download / 5 Mbps upload

---

## Email & Communication

### Q: What is my email storage limit?

**A:** Email quotas are:

| Role | Mailbox Size | Archive Size |
|------|-------------|--------------|
| Standard | 50 GB | 100 GB |
| Manager | 100 GB | 200 GB |
| Executive | Unlimited | Unlimited |

To check usage: Outlook > File > Account Settings > Account Settings > Data Files

---

### Q: How do I set up an out-of-office reply?

**A:** In Outlook:

1. Go to **File > Automatic Replies**
2. Select "Send automatic replies"
3. Set date range (optional)
4. Write your message for internal and external senders
5. Click OK

**Best Practice**: Include your return date and alternate contact.

---

### Q: How do I recall a sent email?

**A:** You can attempt to recall emails sent to other Contoso employees:

1. Go to Sent Items
2. Open the email you want to recall
3. Go to **Message > Actions > Recall This Message**
4. Choose to delete unread copies or replace with new message
5. Click OK

**Note**: Recall only works if the recipient hasn't read the email and is using Outlook within Contoso.

---

### Q: What's the maximum email attachment size?

**A:** 
- **Internal emails**: 150 MB
- **External emails**: 25 MB

For larger files:
- Use OneDrive and share a link
- Use the secure file transfer portal at https://files.contoso.com

---

## Hardware & Software

### Q: How do I request a new laptop or equipment?

**A:** Submit a hardware request:

1. Go to https://itportal.contoso.com
2. Click "Hardware Request"
3. Select equipment type
4. Provide business justification
5. Submit for manager approval

**Standard refresh cycle**: Laptops are replaced every 4 years. You'll receive notification when eligible for refresh.

---

### Q: How do I install software on my company laptop?

**A:** Use the Software Center:

1. Click Start and search for "Software Center"
2. Browse available applications
3. Click "Install" on the desired software
4. Wait for installation to complete

If the software you need isn't listed, submit a software request through the IT Portal.

---

### Q: My laptop is running slowly. What should I do?

**A:** Try these steps:

1. **Restart**: Restart your laptop (not just close the lid)
2. **Updates**: Check for Windows updates (Settings > Update & Security)
3. **Storage**: Ensure at least 20% free disk space
4. **Startup**: Disable unnecessary startup programs
5. **Browser**: Close unused browser tabs
6. **Antivirus**: Run a full system scan

If issues persist, contact IT for a diagnostic appointment.

---

### Q: How do I connect to a printer?

**A:** Printers are auto-deployed based on your office location.

**Manual addition**:
1. Go to **Settings > Devices > Printers & Scanners**
2. Click "Add a printer"
3. Select from the list or search by printer name

**Printer naming convention**: `[Building]-[Floor]-[Type]`  
Example: `HQ-3-Color` = Headquarters, 3rd floor, Color printer

---

## Data & Security

### Q: How do I share files securely with external parties?

**A:** Use OneDrive or SharePoint:

1. Upload file to OneDrive
2. Click "Share"
3. Enter external email address
4. Set permissions (view only recommended)
5. Set expiration date for link
6. Click "Send"

**For sensitive data**: Use the Secure File Transfer portal at https://files.contoso.com which provides encryption and audit logging.

---

### Q: I received a suspicious email. What should I do?

**A:** Report it immediately:

1. **Do NOT** click any links or download attachments
2. Click the "Report Phishing" button in Outlook
3. Or forward to security@contoso.com
4. Delete the email after reporting

**Red flags to watch for**:
- Urgent requests for money or credentials
- Unfamiliar sender addresses
- Grammatical errors
- Links that don't match the displayed text

---

### Q: How do I encrypt a sensitive email?

**A:** Use message encryption:

1. Compose your email
2. Go to **Options > Encrypt**
3. Select encryption level:
   - **Encrypt**: Recipients need to verify identity
   - **Do Not Forward**: Prevents forwarding, copying, printing
   - **Confidential**: Applies company confidential label
4. Send as normal

Recipients outside Contoso will receive instructions to view encrypted content.

---

## Support Contact

**IT Help Desk**  
Phone: x5555 (internal) | 1-800-CONTOSO (external)  
Email: helpdesk@contoso.com  
Portal: https://itportal.contoso.com  
Hours: 24/7 for critical issues | 7 AM - 7 PM ET for general support

**Response Time SLAs**:
- Critical (system down): 15 minutes
- High (unable to work): 2 hours
- Medium (degraded functionality): 8 hours
- Low (questions/how-to): 24 hours

---

*Last Updated: December 2025*
