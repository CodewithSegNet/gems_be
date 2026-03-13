"""SendGrid Email Service"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    HAS_SENDGRID = True
except ImportError:
    HAS_SENDGRID = False
    print("[EMAIL] sendgrid package not installed — emails will be logged to console only")


SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@gemsore.com")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Gems Ore")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@gemsore.com")
APP_URL = os.getenv("APP_URL", "http://127.0.0.1:7001")
SITE_URL = os.getenv("SITE_URL", "https://www.gemsore.com")
LOGO_URL = f"https://res.cloudinary.com/dm1kcchpq/image/upload/v1773167300/logos_jhdsxx.png"

# SMTP config for fast direct delivery
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def _base_template(content: str) -> str:
    """Wrap content in the branded Gems Ore email template."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="margin:0;padding:0;background-color:#f8f6f4;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
      <div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:16px;overflow:hidden;margin-top:20px;margin-bottom:20px;box-shadow:0 4px 24px rgba(0,0,0,0.06);">
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#583931 0%,#7a5248 100%);padding:32px 40px;text-align:center;">
          <img src="{LOGO_URL}" alt="Gems Ore" width="80" height="80" style="display:block;margin:0 auto 12px;" />
          <p style="color:rgba(255,255,255,0.7);font-size:12px;margin:6px 0 0;letter-spacing:2px;text-transform:uppercase;">Handcrafted Luxury Jewelry</p>
        </div>
        <!-- Body -->
        <div style="padding:40px;">
          {content}
        </div>
        <!-- Footer -->
        <div style="background:#f8f6f4;padding:24px 40px;text-align:center;border-top:1px solid #eee;">
          <p style="color:#583931;font-size:13px;font-weight:600;margin:0 0 8px;">Need help? Contact us:</p>
          <p style="color:#666;font-size:12px;margin:0 0 4px;">📞 <a href="tel:+2348052842509" style="color:#583931;text-decoration:none;">+234 8052842509</a></p>
          <p style="color:#666;font-size:12px;margin:0 0 12px;">✉️ <a href="mailto:contact@gemsore.com" style="color:#583931;text-decoration:none;">contact@gemsore.com</a></p>
          <p style="color:#999;font-size:12px;margin:0;">&copy; 2026 Gems Ore. All rights reserved.</p>
          <p style="color:#bbb;font-size:11px;margin:8px 0 0;">This email was sent from Gems Ore. If you didn't expect this, please ignore it.</p>
        </div>
      </div>
    </body>
    </html>
    """


def _send(to_email: str, subject: str, html_body: str):
    """Send an email via SendGrid. Fails silently with a console warning if no API key or module."""
    if not HAS_SENDGRID or not SENDGRID_API_KEY:
        print(f"[EMAIL] {'No sendgrid module' if not HAS_SENDGRID else 'No SENDGRID_API_KEY set'} — skipping email to {to_email} | Subject: {subject}")
        return False
    try:
        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_body),
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        print(f"[EMAIL] Sent '{subject}' to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send to {to_email}: {e}")
        return False


def send_otp_email(to_email: str, otp_code: str):
    """Send OTP verification code via email."""
    content = f"""
      <h2 style="color:#583931;font-size:22px;margin:0 0 16px;">Your Verification Code 🔐</h2>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:0 0 24px;">
        Use the code below to verify your identity. This code expires in <strong>10 minutes</strong>.
      </p>
      <div style="background:linear-gradient(135deg,#583931,#7a5248);border-radius:16px;padding:32px;margin:24px 0;text-align:center;">
        <p style="color:rgba(255,255,255,0.7);font-size:12px;margin:0 0 12px;text-transform:uppercase;letter-spacing:2px;">Verification Code</p>
        <p style="color:#ffffff;font-size:40px;font-weight:700;letter-spacing:12px;margin:0;font-family:'Courier New',monospace;">{otp_code}</p>
      </div>
      <div style="background:#fef3cd;border-radius:10px;padding:16px;margin:20px 0;border-left:4px solid #f59e0b;">
        <p style="color:#92400e;font-size:13px;margin:0;line-height:1.6;">
          ⚠️ <strong>Security tip:</strong> Never share this code with anyone. Gems Ore will never ask you for your verification code.
        </p>
      </div>
      <p style="color:#888;font-size:13px;line-height:1.6;margin:16px 0 0;">
        If you didn't request this code, you can safely ignore this email.
      </p>
    """
    return _send(to_email, f"Your Gems Ore Verification Code: {otp_code}", _base_template(content))


def send_otp_smtp(to_email: str, otp_code: str) -> bool:
    """Send OTP via direct SMTP — much faster than SendGrid SDK on shared hosting."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[SMTP] No SMTP credentials set — skipping SMTP for {to_email}")
        return False
    try:
        subject = f"Your Gems Ore Verification Code: {otp_code}"
        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:20px;">
          <div style="background:linear-gradient(135deg,#583931,#7a5248);border-radius:12px;padding:24px;text-align:center;margin-bottom:16px;">
            <img src="{LOGO_URL}" alt="Gems Ore" width="50" height="50" style="display:block;margin:0 auto 8px;" />
            <p style="color:rgba(255,255,255,0.7);font-size:10px;letter-spacing:2px;text-transform:uppercase;margin:0;">Verification Code</p>
          </div>
          <div style="background:#f8f6f4;border-radius:12px;padding:28px;text-align:center;">
            <p style="color:#583931;font-size:36px;font-weight:700;letter-spacing:10px;margin:0;font-family:'Courier New',monospace;">{otp_code}</p>
          </div>
          <p style="color:#888;font-size:12px;text-align:center;margin-top:12px;">This code expires in 10 minutes. Do not share it.</p>
        </div>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SENDGRID_FROM_NAME} <{SMTP_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=10) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f"[SMTP] OTP sent to {to_email} successfully")
        return True
    except Exception as e:
        print(f"[SMTP] Failed to send OTP to {to_email}: {e}")
        return False


def send_otp_background(to_email: str, otp_code: str):
    """Background task: retry OTP via SendGrid if SMTP failed."""
    print(f"[BACKGROUND] Retrying OTP send to {to_email} via SendGrid...")
    result = send_otp_email(to_email, otp_code)
    if result:
        print(f"[BACKGROUND] SendGrid backup succeeded for {to_email}")
    else:
        print(f"[BACKGROUND] SendGrid backup also failed for {to_email}")


def send_welcome_email(to_email: str, first_name: str = None):
    """Send welcome email after successful signup."""
    name = first_name or "there"
    content = f"""
      <h2 style="color:#583931;font-size:22px;margin:0 0 16px;">Welcome aboard, {name}! 🎉</h2>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:0 0 16px;">
        We're absolutely thrilled to have you join the Gems Ore family. Your account has been created successfully and you're all set to explore our exquisite collection.
      </p>
      <div style="background:#f8f6f4;border-radius:12px;padding:24px;margin:24px 0;border-left:4px solid #583931;">
        <p style="color:#583931;font-size:14px;font-weight:600;margin:0 0 8px;">What you can do now:</p>
        <ul style="color:#666;font-size:14px;line-height:2;margin:0;padding-left:20px;">
          <li>Browse our handcrafted jewelry collection</li>
          <li>Save your favorites to your wishlist</li>
          <li>Get exclusive member-only discounts</li>
          <li>Track your orders in real-time</li>
        </ul>
      </div>
      <div style="text-align:center;margin:32px 0 16px;">
        <a href="https://www.gemsore.com/" style="background:linear-gradient(135deg,#583931,#7a5248);color:white;padding:14px 40px;text-decoration:none;border-radius:10px;font-size:15px;font-weight:600;display:inline-block;">
          Start Shopping &rarr;
        </a>
      </div>
    """
    _send(to_email, "Welcome to Gems Ore! 💎", _base_template(content))


def send_login_notification(to_email: str, first_name: str = None):
    """Send login notification email."""
    name = first_name or "there"
    from datetime import datetime
    login_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    content = f"""
      <h2 style="color:#583931;font-size:22px;margin:0 0 16px;">Welcome back, {name}! 👋</h2>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:0 0 16px;">
        You've successfully signed in to your Gems Ore account.
      </p>
      <div style="background:#f8f6f4;border-radius:12px;padding:20px;margin:20px 0;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="color:#888;font-size:13px;padding:6px 0;">Login Time</td><td style="color:#444;font-size:13px;padding:6px 0;text-align:right;font-weight:600;">{login_time}</td></tr>
          <tr><td style="color:#888;font-size:13px;padding:6px 0;">Email</td><td style="color:#444;font-size:13px;padding:6px 0;text-align:right;font-weight:600;">{to_email}</td></tr>
        </table>
      </div>
      <p style="color:#888;font-size:13px;line-height:1.6;margin:20px 0 0;">
        If this wasn't you, please secure your account immediately by changing your password.
      </p>
    """
    _send(to_email, "New login to your Gems Ore account 🔐", _base_template(content))


def send_order_confirmation(to_email: str, order_id: str, total: float, customer_name: str = None, estimated_delivery: str = None):
    """Send order confirmation email."""
    name = customer_name or "Customer"
    delivery_html = ""
    if estimated_delivery:
        delivery_html = f"""
      <div style="background:#f8f6f4;border-radius:12px;padding:20px;margin:20px 0;text-align:center;border:1px solid #e8e0db;">
        <p style="color:#583931;font-size:13px;margin:0 0 6px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">🚚 Estimated Delivery</p>
        <p style="color:#583931;font-size:22px;font-weight:700;margin:0;">{estimated_delivery}</p>
      </div>
"""
    content = f"""
      <h2 style="color:#583931;font-size:22px;margin:0 0 16px;">Order Confirmed! ✨</h2>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:0 0 16px;">Hi {name},</p>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:0 0 20px;">
        Your order has been received and is being processed. Here are your order details:
      </p>
      <div style="background:linear-gradient(135deg,#583931,#7a5248);border-radius:12px;padding:28px;margin:24px 0;text-align:center;">
        <p style="color:rgba(255,255,255,0.7);font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">Order Total</p>
        <p style="color:#fff;font-size:32px;font-weight:700;margin:0;">&#8358;{total:,.2f}</p>
        <p style="color:rgba(255,255,255,0.5);font-size:12px;margin:12px 0 0;font-family:monospace;">Order #{order_id[:12]}...</p>
      </div>
      {delivery_html}
      <p style="color:#444;font-size:15px;line-height:1.7;margin:16px 0;">
        We'll send you updates as your order progresses. Thank you for shopping with Gems Ore!
      </p>
    """
    _send(to_email, f"Order #{order_id[:8]} Confirmed! ✨", _base_template(content))


def send_order_status_update(to_email: str, order_id: str, new_status: str, customer_name: str = None, cancellation_reason: str = None):
    """Send email when order status changes."""
    name = customer_name or "Customer"
    status_config = {
        "processing": ("🔄", "#2563eb", "Being Processed", "Great news! Your order is now being prepared by our artisans. We'll notify you once it's ready for delivery."),
        "completed": ("✅", "#16a34a", "Completed", "Your order has been completed! We hope you absolutely love your new jewelry. Thank you for choosing Gems Ore."),
        "cancelled": ("❌", "#dc2626", "Cancelled", "Your order has been cancelled. If you have any questions or concerns, please don't hesitate to reach out to our support team."),
        "pending": ("⏳", "#d97706", "Pending", "Your order is pending. We'll begin processing it shortly."),
        "shipped": ("📦", "#7c3aed", "Shipped", "Your order is on its way! You should receive it within the estimated delivery timeframe."),
    }
    emoji, color, label, message = status_config.get(new_status, ("📋", "#583931", new_status.replace("_", " ").title(), "Your order status has been updated."))
    content = f"""
      <h2 style="color:#583931;font-size:22px;margin:0 0 16px;">Order Status Update</h2>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:0 0 20px;">Hi {name},</p>
      <div style="background:#f8f6f4;border-radius:12px;padding:24px;margin:20px 0;text-align:center;border:2px solid {color}20;">
        <span style="font-size:36px;">{emoji}</span>
        <p style="color:{color};font-size:18px;font-weight:700;margin:12px 0 4px;">{label}</p>
        <p style="color:#888;font-size:12px;font-family:monospace;margin:0;">Order #{order_id[:12]}...</p>
      </div>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:16px 0;">{message}</p>
      {f'''
      <div style="background:#fef2f2;border-radius:10px;padding:16px 20px;margin:16px 0;border-left:4px solid #dc2626;">
        <p style="color:#991b1b;font-size:13px;font-weight:600;margin:0 0 4px;">Reason for Cancellation:</p>
        <p style="color:#444;font-size:14px;margin:0;">{cancellation_reason}</p>
      </div>
      ''' if new_status == 'cancelled' and cancellation_reason else ''}
    """
    _send(to_email, f"Order #{order_id[:8]} — {label}", _base_template(content))


def send_delivery_status_update(to_email: str, order_id: str, delivery_status: str, customer_name: str = None):
    """Send email when delivery status changes (shipped, in_transit, delivered)."""
    name = customer_name or "Customer"
    status_config = {
        "shipped": ("📦", "#7c3aed", "Shipped", "Great news! Your order has been shipped and is on its way to you. You should receive it within the estimated delivery timeframe."),
        "in_transit": ("🚚", "#2563eb", "In Transit", "Your order is currently in transit and will be delivered soon. Sit tight — it's almost there!"),
        "delivered": ("✅", "#16a34a", "Delivered", "Your order has been delivered! We hope you love your new jewelry. Thank you for shopping with Gems Ore."),
        "not_shipped": ("⏳", "#d97706", "Not Yet Shipped", "Your order is being prepared and will be shipped soon."),
    }
    emoji, color, label, message = status_config.get(delivery_status, ("📋", "#583931", delivery_status.replace("_", " ").title(), "Your delivery status has been updated."))
    content = f"""
      <h2 style="color:#583931;font-size:22px;margin:0 0 16px;">Delivery Status Update</h2>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:0 0 20px;">Hi {name},</p>
      <div style="background:#f8f6f4;border-radius:12px;padding:24px;margin:20px 0;text-align:center;border:2px solid {color}20;">
        <span style="font-size:36px;">{emoji}</span>
        <p style="color:{color};font-size:18px;font-weight:700;margin:12px 0 4px;">{label}</p>
        <p style="color:#888;font-size:12px;font-family:monospace;margin:0;">Order #{order_id[:12]}...</p>
      </div>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:16px 0;">{message}</p>
      <div style="text-align:center;margin:24px 0;">
        <a href="https://www.gemsore.com/history" style="background:linear-gradient(135deg,#583931,#7a5248);color:white;padding:12px 32px;text-decoration:none;border-radius:10px;font-size:14px;font-weight:600;display:inline-block;">
          Track Your Order &rarr;
        </a>
      </div>
    """
    _send(to_email, f"Order #{order_id[:8]} — {label} {emoji}", _base_template(content))


def send_admin_payment_notification(order_id: str, customer_email: str, total: float, payment_method: str, customer_name: str = None):
    """Notify admin when a payment is made or proof uploaded."""
    name = customer_name or customer_email
    content = f"""
      <h2 style="color:#583931;font-size:22px;margin:0 0 16px;">💰 New Payment Received</h2>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:0 0 20px;">
        A new payment has been made and requires your attention.
      </p>
      <div style="background:#f8f6f4;border-radius:12px;padding:24px;margin:20px 0;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="color:#888;font-size:13px;padding:8px 0;border-bottom:1px solid #eee;">Customer</td><td style="color:#444;font-size:13px;padding:8px 0;text-align:right;font-weight:600;border-bottom:1px solid #eee;">{name}</td></tr>
          <tr><td style="color:#888;font-size:13px;padding:8px 0;border-bottom:1px solid #eee;">Email</td><td style="color:#444;font-size:13px;padding:8px 0;text-align:right;font-weight:600;border-bottom:1px solid #eee;">{customer_email}</td></tr>
          <tr><td style="color:#888;font-size:13px;padding:8px 0;border-bottom:1px solid #eee;">Order ID</td><td style="color:#444;font-size:13px;padding:8px 0;text-align:right;font-weight:600;font-family:monospace;border-bottom:1px solid #eee;">#{order_id[:12]}</td></tr>
          <tr><td style="color:#888;font-size:13px;padding:8px 0;border-bottom:1px solid #eee;">Amount</td><td style="color:#583931;font-size:16px;padding:8px 0;text-align:right;font-weight:700;border-bottom:1px solid #eee;">&#8358;{total:,.2f}</td></tr>
          <tr><td style="color:#888;font-size:13px;padding:8px 0;">Payment Method</td><td style="color:#444;font-size:13px;padding:8px 0;text-align:right;font-weight:600;">{payment_method}</td></tr>
        </table>
      </div>
      <div style="text-align:center;margin:24px 0;">
        <a href="https://www.gemsore.com/admin/orders" style="background:linear-gradient(135deg,#583931,#7a5248);color:white;padding:12px 32px;text-decoration:none;border-radius:10px;font-size:14px;font-weight:600;display:inline-block;">
          View in Dashboard &rarr;
        </a>
      </div>
    """
    _send(ADMIN_EMAIL, f"💰 New Payment — Order #{order_id[:8]} (₦{total:,.0f})", _base_template(content))


def send_subscription_confirmation(to_email: str):
    """Send newsletter subscription confirmation."""
    content = """
      <h2 style="color:#583931;font-size:22px;margin:0 0 16px;">You're Subscribed! 🎉</h2>
      <p style="color:#444;font-size:15px;line-height:1.7;margin:0 0 20px;">
        Welcome to the Gems Ore inner circle! You'll be the first to know about everything exciting.
      </p>
      <div style="background:#f8f6f4;border-radius:12px;padding:24px;margin:20px 0;border-left:4px solid #583931;">
        <p style="color:#583931;font-size:14px;font-weight:600;margin:0 0 12px;">What to expect:</p>
        <ul style="color:#666;font-size:14px;line-height:2.2;margin:0;padding-left:20px;">
          <li>✨ New collection launches &amp; exclusive previews</li>
          <li>🏷️ Member-only discounts and flash sales</li>
          <li>💡 Jewelry care tips and styling inspiration</li>
          <li>🎁 Special birthday and anniversary surprises</li>
        </ul>
      </div>
      <div style="text-align:center;margin:28px 0 12px;">
        <a href="https://www.gemsore.com/" style="background:linear-gradient(135deg,#583931,#7a5248);color:white;padding:14px 40px;text-decoration:none;border-radius:10px;font-size:15px;font-weight:600;display:inline-block;">
          Browse New Arrivals &rarr;
        </a>
      </div>
    """
    _send(to_email, "Welcome to the Gems Ore Newsletter! 💎", _base_template(content))
