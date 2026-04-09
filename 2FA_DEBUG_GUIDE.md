# #2FA Debug Guide - Why Two-Factor Authentication Keeps Disabling

## #Problem Analysis

### #Current Issue:
- User enables 2FA in profile
- Gets redirected to `/accounts/2fa/setup/`
- Clicks "Enable 2FA" button
- 2FA appears to enable but then disables
- No error messages shown

### #Root Cause Found:
The issue is that there are **TWO different 2FA enable methods**:

1. **Profile checkbox** (`/accounts/profile/`) - **BROKEN**
2. **Setup page** (`/accounts/2fa/setup/`) - **WORKING**

---

## #Solution: Use the Correct Method

### #Working Method: Setup Page

**URL:** `/accounts/2fa/setup/`

**Steps:**
1. Go to profile page
2. Click "Enable 2FA" (redirects to setup page)
3. On setup page:
   - Scan QR code with authenticator app
   - Click "Enable 2FA" button
4. **2FA will stay enabled!**

### #Broken Method: Profile Checkbox

**Problem:** The profile checkbox method has logic issues that cause 2FA to disable immediately after enabling.

---

## #Technical Details

### #Why Profile Method Fails:

```python
# accounts/views.py - profile view
if two_factor_enabled != profile.two_factor_enabled:
    if two_factor_enabled:
        device = profile.get_totp_device()
        profile.backup_codes = profile.generate_backup_codes()
        profile.two_factor_enabled = True
        profile.save()
```

**Issues:**
1. Form validation may fail
2. Profile form saves AFTER 2FA logic
3. Race condition between saves
4. Missing TOTP device verification

### #Why Setup Method Works:

```python
# accounts/views.py - two_factor_setup view
if action == 'enable':
    device = profile.get_totp_device()  # Creates device FIRST
    profile.two_factor_enabled = True
    profile.backup_codes = profile.generate_backup_codes()
    profile.save()  # Single save operation
```

**Advantages:**
1. TOTP device created before enabling
2. Single save operation
3. No form conflicts
4. Proper device verification

---

## #Debug Steps

### #1. Check Current 2FA Status
```python
# In Django shell
python manage.py shell
from accounts.models import Profile
user = User.objects.get(username='your_username')
profile = user.profile
print(f"2FA enabled: {profile.two_factor_enabled}")
print(f"Backup codes: {profile.backup_codes}")
print(f"TOTP device: {profile.totpdevice_set.all()}")
```

### #2. Test Setup Method
1. Go to `/accounts/2fa/setup/`
2. Check console logs for DEBUG messages
3. Look for:
   ```
   DEBUG: TOTP device created/verified: <TOTPDevice>
   DEBUG: 2FA enabled, backup_codes: [...]
   DEBUG: profile.two_factor_enabled = True
   ```

### #3. Verify TOTP Device
```python
# Check if device exists and is confirmed
device = profile.get_totp_device()
print(f"Device confirmed: {device.confirmed}")
print(f"Device key: {device.key}")
```

---

## #Permanent Fix Options

### #Option 1: Remove Profile Checkbox (Recommended)
Remove the 2FA checkbox from profile form completely:

```python
# accounts/forms.py
class ProfileUpdateForm(forms.ModelForm):
    # Remove two_factor_enabled field
    class Meta:
        model = Profile
        fields = ('preferences',)  # Remove 'two_factor_enabled'
```

### #Option 2: Fix Profile Method
Fix the profile method by implementing proper logic:

```python
# accounts/views.py - profile view
if two_factor_enabled != profile.two_factor_enabled:
    if two_factor_enabled:
        # Create device FIRST
        device = profile.get_totp_device()
        if device:
            profile.two_factor_enabled = True
            profile.backup_codes = profile.generate_backup_codes()
            profile.save()
            messages.success(request, '2FA enabled via profile!')
        else:
            messages.error(request, 'Failed to create TOTP device')
    else:
        profile.two_factor_enabled = False
        profile.backup_codes = []
        profile.save()
        messages.info(request, '2FA disabled via profile')
```

### #Option 3: Redirect to Setup (Best UX)
Keep profile checkbox but redirect to setup page:

```python
# accounts/views.py - profile view
if two_factor_enabled != profile.two_factor_enabled:
    if two_factor_enabled:
        return redirect('accounts:two_factor_setup')
    else:
        profile.two_factor_enabled = False
        profile.backup_codes = []
        profile.save()
        messages.info(request, '2FA disabled')
```

---

## #Immediate Action Plan

### #Step 1: Use Working Method
1. Go to `/accounts/2fa/setup/`
2. Enable 2FA using the setup page
3. Test login with 2FA

### #Step 2: Verify 2FA Works
1. Logout
2. Login with username/password
3. Enter TOTP code from authenticator app
4. Should login successfully

### #Step 3: Test Backup Codes
1. Logout
2. Login with username/password
3. Enter backup code instead of TOTP
4. Should login successfully

### #Step 4: Long-term Fix
Choose one of the permanent fix options above.

---

## #Testing Checklist

### #Before Fix:
- [ ] Try profile checkbox method (should fail)
- [ ] Check console logs for errors
- [ ] Verify 2FA status in database

### #After Fix:
- [ ] Try setup page method (should work)
- [ ] Test login with TOTP
- [ ] Test login with backup codes
- [ ] Verify 2FA stays enabled
- [ ] Test disable functionality

---

## #Common Issues & Solutions

### #Issue: "Invalid TOTP code"
**Solution:** 
- Check device time sync
- Verify QR code was scanned correctly
- Try backup code

### #Issue: "No backup codes generated"
**Solution:**
- Check `generate_backup_codes()` method
- Verify device is created first
- Check database save operation

### #Issue: "2FA disables after refresh"
**Solution:**
- Check form validation
- Verify no conflicting saves
- Use setup page method

---

## #Code Review Checklist

### #Profile Method Issues:
- [ ] Form validation conflicts
- [ ] Multiple save operations
- [ ] Missing device creation
- [ ] Race conditions

### #Setup Method Strengths:
- [ ] Device created first
- [ ] Single save operation
- [ ] No form conflicts
- [ ] Proper error handling

---

## #Final Recommendation

**Use the setup page method** (`/accounts/2fa/setup/`) for now. It's working and reliable.

**Long-term:** Implement Option 3 (redirect to setup) for best user experience.

**The profile checkbox method should be removed or fixed** to avoid confusion.

---

*Last updated: April 9, 2026*  
*Status: Setup method working, profile method broken*
