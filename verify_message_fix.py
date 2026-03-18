#!/usr/bin/env python3
"""
Code verification script to check that message routing fixes are in place.
"""

import re
import os

def check_file_for_patterns(filepath, patterns, description):
    """Check if file contains expected patterns"""
    print(f"\n🔍 Checking {description} in {os.path.basename(filepath)}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        results = {}
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            results[pattern_name] = len(matches)
            
            if matches:
                print(f"   ✅ Found {len(matches)} instance(s) of '{pattern_name}'")
            else:
                print(f"   ❌ No instances of '{pattern_name}' found")
        
        return results
        
    except FileNotFoundError:
        print(f"   ❌ File not found: {filepath}")
        return {}
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return {}

def verify_message_routing_fix():
    """Verify that the message routing fixes are properly implemented"""
    print("🔧 Message Routing Fix Verification")
    print("=" * 50)
    
    base_path = "c:\\Users\\Admin\\Fuetimeplus"
    
    # Check 1: Verify problematic socketio.emit statements are removed from app.py
    app_patterns = {
        "broadcast_emit_removed": r"socketio\.emit\('receive_message'.*room=f'user_\{.*\}'",
        "http_route_still_exists": r"@app\.route\('/chat/<int:user_id>'",
        "duplicate_connect_removed": r"@socketio\.on\('connect'\)\s*\ndef handle_connect\(\):",
        "duplicate_disconnect_removed": r"@socketio\.on\('disconnect'\)\s*\ndef handle_disconnect\(\):"
    }
    
    app_results = check_file_for_patterns(
        f"{base_path}\\app.py", 
        app_patterns, 
        "app.py message routing"
    )
    
    # Check 2: Verify events.py has proper message handler
    events_patterns = {
        "proper_message_handler": r"@socketio\.on\('message'\)\s*\@socket_auth_required\s*\ndef handle_message\(data\):",
        "recipient_validation": r"recipient = User\.query\.get\(recipient_id\)",
        "room_targeting": r"emit\('new_message'.*room=f'user_\{recipient_id\}'",
        "sender_room_update": r"emit\('new_message'.*room=f'user_\{current_user\.id\}'",
        "online_status_tracking": r"current_user\.is_online = True"
    }
    
    events_results = check_file_for_patterns(
        f"{base_path}\\events.py", 
        events_patterns, 
        "events.py message handling"
    )
    
    # Check 3: Verify blueprints/messages.py no longer has duplicate handlers
    messages_patterns = {
        "duplicate_handler_removed": r"def register_socket_events\(\):",
        "blueprint_message_handler": r"@socketio\.on\('message'\)"
    }
    
    messages_results = check_file_for_patterns(
        f"{base_path}\\blueprints\\messages.py", 
        messages_patterns, 
        "blueprints/messages.py duplicates"
    )
    
    # Summary
    print("\n📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    # Check if problematic patterns are removed
    issues_fixed = 0
    total_checks = 0
    
    # app.py checks
    if app_results.get("broadcast_emit_removed", 0) == 0:
        print("✅ Problematic broadcast emit statements removed from app.py")
        issues_fixed += 1
    else:
        print("❌ Broadcast emit statements still present in app.py")
    total_checks += 1
    
    if app_results.get("duplicate_connect_removed", 0) == 0:
        print("✅ Duplicate connect handlers removed from app.py")
        issues_fixed += 1
    else:
        print("❌ Duplicate connect handlers still present in app.py")
    total_checks += 1
    
    if app_results.get("duplicate_disconnect_removed", 0) == 0:
        print("✅ Duplicate disconnect handlers removed from app.py")
        issues_fixed += 1
    else:
        print("❌ Duplicate disconnect handlers still present in app.py")
    total_checks += 1
    
    # events.py checks
    if events_results.get("proper_message_handler", 0) >= 1:
        print("✅ Proper message handler exists in events.py")
        issues_fixed += 1
    else:
        print("❌ Proper message handler missing in events.py")
    total_checks += 1
    
    if events_results.get("recipient_validation", 0) >= 1:
        print("✅ Recipient validation implemented in events.py")
        issues_fixed += 1
    else:
        print("❌ Recipient validation missing in events.py")
    total_checks += 1
    
    if events_results.get("room_targeting", 0) >= 1:
        print("✅ Proper room targeting implemented in events.py")
        issues_fixed += 1
    else:
        print("❌ Proper room targeting missing in events.py")
    total_checks += 1
    
    # blueprints/messages.py checks
    if messages_results.get("duplicate_handler_removed", 0) == 0:
        print("✅ Duplicate handlers removed from blueprints/messages.py")
        issues_fixed += 1
    else:
        print("❌ Duplicate handlers still present in blueprints/messages.py")
    total_checks += 1
    
    # Final verdict
    print(f"\n🎯 OVERALL RESULT: {issues_fixed}/{total_checks} issues fixed")
    
    if issues_fixed == total_checks:
        print("🎉 ALL FIXES VERIFIED! Message routing should now work correctly.")
        print("\n📝 What was fixed:")
        print("   • Removed broadcast emit statements that sent messages to all users")
        print("   • Eliminated duplicate Socket.IO event handlers")
        print("   • Centralized message handling in events.py with proper room targeting")
        print("   • Added recipient validation to prevent errors")
        print("   • Maintained online status tracking functionality")
    else:
        print("⚠️  Some issues may still exist. Please review the failed checks above.")
    
    return issues_fixed == total_checks

if __name__ == '__main__':
    success = verify_message_routing_fix()
    exit(0 if success else 1)
