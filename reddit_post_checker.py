import csv
import requests
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from datetime import datetime

# Email Configuration
SENDER_EMAIL = "data10710172@gmail.com"
SENDER_PASSWORD = "Allan@20205"
RECIPIENT_EMAIL = "allanngetich50@gmail.com"

def check_reddit_post(url):
    """
    Check if a Reddit post is still live.
    Returns: ('live', 'removed', 'deleted', 'error')
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            return 'not_found'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().lower()
        
        # Check for removal/deletion indicators
        if '[removed]' in page_text or 'this post was removed' in page_text:
            return 'removed'
        elif '[deleted]' in page_text or 'this post was deleted' in page_text:
            return 'deleted'
        elif response.status_code == 200:
            return 'live'
        else:
            return 'error'
            
    except requests.exceptions.RequestException as e:
        print(f"Error checking post: {e}")
        return 'error'

def send_email(subject, body):
    """Send email alert via Gmail SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        server.send_message(msg)
        server.quit()
        
        print(f"\n✓ Alert email sent to {RECIPIENT_EMAIL}")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to send email: {e}")
        return False

def generate_alert_email(removed_posts, deleted_posts, not_found_posts, check_time):
    """Generate email alert for removed/deleted posts."""
    
    total_issues = len(removed_posts) + len(deleted_posts) + len(not_found_posts)
    
    report = f"""
⚠️ REDDIT POST REMOVAL ALERT ⚠️
{'='*60}
Check Date: {check_time.strftime('%Y-%m-%d %H:%M:%S')}
Posts with Issues: {total_issues}

"""
    
    if removed_posts:
        report += f"\n🚫 REMOVED POSTS ({len(removed_posts)}):\n"
        report += f"{'-'*60}\n"
        for url in removed_posts:
            report += f"{url}\n\n"
    
    if deleted_posts:
        report += f"\n🗑️  DELETED POSTS ({len(deleted_posts)}):\n"
        report += f"{'-'*60}\n"
        for url in deleted_posts:
            report += f"{url}\n\n"
    
    if not_found_posts:
        report += f"\n❓ NOT FOUND / 404 ({len(not_found_posts)}):\n"
        report += f"{'-'*60}\n"
        for url in not_found_posts:
            report += f"{url}\n\n"
    
    report += f"\n{'='*60}\n"
    report += "Action Required: Review the above posts\n"
    
    return report

def main():
    input_file = 'posts.csv'
    
    check_time = datetime.now()
    
    # Read post URLs from CSV
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            post_urls = [row[0].strip() for row in reader if row and row[0].strip()]
    except FileNotFoundError:
        print(f"Error: {input_file} not found!")
        return
    
    if not post_urls:
        print("No posts found in posts.csv")
        return
    
    print(f"Checking {len(post_urls)} Reddit posts...\n")
    
    # Track results
    live_posts = []
    removed_posts = []
    deleted_posts = []
    not_found_posts = []
    error_posts = []
    
    # Check each post
    for i, url in enumerate(post_urls, 1):
        print(f"[{i}/{len(post_urls)}] Checking post...", end=' ')
        
        status = check_reddit_post(url)
        
        if status == 'live':
            live_posts.append(url)
            print("✓ LIVE")
        elif status == 'removed':
            removed_posts.append(url)
            print("✗ REMOVED")
        elif status == 'deleted':
            deleted_posts.append(url)
            print("✗ DELETED")
        elif status == 'not_found':
            not_found_posts.append(url)
            print("✗ NOT FOUND")
        else:
            error_posts.append(url)
            print("? ERROR")
        
        # Rate limiting
        if i < len(post_urls):
            time.sleep(10)
    
    # Print summary
    print(f"\n{'='*50}")
    print("CHECK SUMMARY:")
    print(f"{'='*50}")
    print(f"LIVE: {len(live_posts)}")
    print(f"REMOVED: {len(removed_posts)}")
    print(f"DELETED: {len(deleted_posts)}")
    print(f"NOT FOUND: {len(not_found_posts)}")
    print(f"ERRORS: {len(error_posts)}")
    
    # Send email ONLY if there are issues
    if removed_posts or deleted_posts or not_found_posts:
        print(f"\n⚠️  Issues detected! Sending alert email...")
        report = generate_alert_email(removed_posts, deleted_posts, not_found_posts, check_time)
        subject = f"🚨 Reddit Post Removal Alert - {len(removed_posts) + len(deleted_posts) + len(not_found_posts)} Posts Affected"
        send_email(subject, report)
    else:
        print(f"\n✓ All posts are live. No email sent.")

if __name__ == "__main__":
    main()
```

## **How to Use:**

### **1. Create your `posts.csv` file:**
Just one URL per line, no headers:
```
https://reddit.com/r/AskReddit/comments/abc123/title_here/
https://reddit.com/r/funny/comments/def456/another_post/
https://reddit.com/r/technology/comments/ghi789/tech_post/
