import csv
import requests
import time
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from datetime import datetime

# Email Configuration
SENDER_EMAIL = "data10710172@gmail.com"
SENDER_PASSWORD = "yydi xacw kczw zmsd"
RECIPIENT_EMAIL = "allanngetich50@gmail.com"

def check_reddit_profile(username):
    """
    Check if a Reddit profile is banned/suspended.
    Returns: ('active', 'banned', 'suspended', 'not_found', or 'error')
    """
    url = f"https://reddit.com/user/{username}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            return 'not_found'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().lower()
        
        if 'suspended' in page_text or 'account has been suspended' in page_text:
            return 'suspended'
        elif 'banned' in page_text:
            return 'banned'
        elif response.status_code == 200:
            return 'active'
        else:
            return 'error'
            
    except requests.exceptions.RequestException as e:
        print(f"Error checking {username}: {e}")
        return 'error'

def load_previous_results(filename='profile_status.csv'):
    """Load previous results to compare changes."""
    previous = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        previous[row[0]] = row[1]
        except Exception as e:
            print(f"Could not load previous results: {e}")
    return previous

def send_email(subject, body):
    """Send email report via Gmail SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        server.send_message(msg)
        server.quit()
        
        print(f"\n✓ Email sent successfully to {RECIPIENT_EMAIL}")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to send email: {e}")
        return False

def generate_report(results, previous_results, start_time, end_time):
    """Generate detailed email report."""
    
    # Calculate statistics
    status_counts = {}
    for _, status in results:
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Detect changes
    changes = {
        'newly_banned': [],
        'newly_suspended': [],
        'newly_active': [],
        'newly_not_found': [],
        'new_accounts': []
    }
    
    current_usernames = {username for username, _ in results}
    previous_usernames = set(previous_results.keys())
    
    for username, current_status in results:
        if username not in previous_results:
            changes['new_accounts'].append(username)
        else:
            previous_status = previous_results[username]
            if previous_status != current_status:
                if current_status == 'banned':
                    changes['newly_banned'].append(f"{username} (was {previous_status})")
                elif current_status == 'suspended':
                    changes['newly_suspended'].append(f"{username} (was {previous_status})")
                elif current_status == 'active' and previous_status in ['banned', 'suspended']:
                    changes['newly_active'].append(f"{username} (was {previous_status})")
                elif current_status == 'not_found':
                    changes['newly_not_found'].append(f"{username} (was {previous_status})")
    
    # Build email body
    duration = (end_time - start_time).total_seconds()
    
    report = f"""
REDDIT PROFILE STATUS REPORT
{'='*60}
Scan Date: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration:.1f} seconds
Total Profiles Checked: {len(results)}

CURRENT STATUS SUMMARY
{'='*60}
"""
    
    for status, count in sorted(status_counts.items()):
        report += f"{status.upper()}: {count}\n"
    
    # Changes section
    has_changes = any(len(v) > 0 for v in changes.values())
    
    if has_changes:
        report += f"\n\nCHANGES DETECTED\n{'='*60}\n"
        
        if changes['newly_banned']:
            report += f"\n🚫 NEWLY BANNED ({len(changes['newly_banned'])}):\n"
            for item in changes['newly_banned']:
                report += f"  - {item}\n"
        
        if changes['newly_suspended']:
            report += f"\n⚠️  NEWLY SUSPENDED ({len(changes['newly_suspended'])}):\n"
            for item in changes['newly_suspended']:
                report += f"  - {item}\n"
        
        if changes['newly_active']:
            report += f"\n✓ BECAME ACTIVE ({len(changes['newly_active'])}):\n"
            for item in changes['newly_active']:
                report += f"  - {item}\n"
        
        if changes['newly_not_found']:
            report += f"\n❓ NOW NOT FOUND ({len(changes['newly_not_found'])}):\n"
            for item in changes['newly_not_found']:
                report += f"  - {item}\n"
        
        if changes['new_accounts']:
            report += f"\n➕ NEW ACCOUNTS CHECKED ({len(changes['new_accounts'])}):\n"
            for item in changes['new_accounts']:
                report += f"  - {item}\n"
    else:
        report += f"\n\nCHANGES DETECTED\n{'='*60}\n"
        report += "No changes detected since last scan.\n"
    
    # Full account list by status
    report += f"\n\nFULL ACCOUNT LIST BY STATUS\n{'='*60}\n"
    
    for status in sorted(status_counts.keys()):
        accounts = [username for username, s in results if s == status]
        report += f"\n{status.upper()} ({len(accounts)}):\n"
        for username in sorted(accounts):
            report += f"  - {username}\n"
    
    report += f"\n{'='*60}\n"
    report += "End of Report\n"
    
    return report

def main():
    input_file = 'profiles.csv'
    output_file = 'profile_status.csv'
    
    start_time = datetime.now()
    
    # Load previous results for comparison
    previous_results = load_previous_results(output_file)
    
    results = []
    
    # Read usernames from CSV
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            usernames = [row[0].strip() for row in reader if row]
    except FileNotFoundError:
        print(f"Error: {input_file} not found!")
        return
    
    print(f"Checking {len(usernames)} profiles...\n")
    
    # Check each profile
    for i, username in enumerate(usernames, 1):
        print(f"[{i}/{len(usernames)}] Checking u/{username}...", end=' ')
        
        status = check_reddit_profile(username)
        results.append([username, status])
        
        print(status.upper())
        
        # Rate limiting - wait between requests
        if i < len(usernames):
            time.sleep(10)
    
    end_time = datetime.now()
    
    # Save results to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Username', 'Status'])
        writer.writerows(results)
    
    # Print console summary
    print(f"\n{'='*50}")
    print("SUMMARY:")
    print(f"{'='*50}")
    
    status_counts = {}
    for _, status in results:
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in sorted(status_counts.items()):
        print(f"{status.upper()}: {count}")
    
    print(f"\nResults saved to {output_file}")
    
    # Generate and send email report
    report = generate_report(results, previous_results, start_time, end_time)
    subject = f"Reddit Profile Status Report - {end_time.strftime('%Y-%m-%d %H:%M')}"
    
    send_email(subject, report)

if __name__ == "__main__":

    main()
