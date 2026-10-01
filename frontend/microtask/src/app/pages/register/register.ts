import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/AuthService';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.css'
})
export class RegisterComponent {
  fullName = '';
  phoneNumber = '';
  password = '';
  confirmPassword = '';

  // Field-level validation messages, shown as the user types/leaves a field
  fullNameError = '';
  phoneNumberError = '';
  passwordError = '';
  confirmPasswordError = '';

  // Server-side errors (e.g. "already registered") surfaced on the right field
  serverError = '';
  successMessage = '';

  isLoading = false;

  private readonly PHONE_REGEX = /^0\d{9}$/; // 07XXXXXXXX / 01XXXXXXXX

  constructor(
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  // ---------- Live field validation ----------

  validateFullName(): void {
    const name = this.fullName.trim();
    if (!name) {
      this.fullNameError = '';
    } else if (/\d/.test(name)) {
      this.fullNameError = 'Full name cannot contain numbers.';
    } else if (name.length < 3) {
      this.fullNameError = 'Full name must be at least 3 characters.';
    } else {
      this.fullNameError = '';
    }
  }

  validatePhoneNumber(): void {
    this.serverError = ''; // clear any stale "already registered" message once they edit it
    const phone = this.phoneNumber.trim();
    if (!phone) {
      this.phoneNumberError = '';
    } else if (!this.PHONE_REGEX.test(phone)) {
      this.phoneNumberError = 'Enter a valid phone number, e.g. 0712345678.';
    } else {
      this.phoneNumberError = '';
    }
  }

  validatePassword(): void {
    if (!this.password) {
      this.passwordError = '';
    } else if (this.password.length < 6) {
      this.passwordError = 'Password must be at least 6 characters.';
    } else {
      this.passwordError = '';
    }
    this.validateConfirmPassword();
  }

  validateConfirmPassword(): void {
    if (!this.confirmPassword) {
      this.confirmPasswordError = '';
    } else if (this.confirmPassword !== this.password) {
      this.confirmPasswordError = 'Passwords do not match.';
    } else {
      this.confirmPasswordError = '';
    }
  }

  private runAllValidations(): boolean {
    this.validateFullName();
    this.validatePhoneNumber();
    this.validatePassword();
    this.validateConfirmPassword();

    if (!this.fullName.trim() || !this.phoneNumber.trim() || !this.password || !this.confirmPassword) {
      if (!this.fullName.trim()) this.fullNameError = 'Full name is required.';
      if (!this.phoneNumber.trim()) this.phoneNumberError = 'Phone number is required.';
      if (!this.password) this.passwordError = 'Password is required.';
      if (!this.confirmPassword) this.confirmPasswordError = 'Please confirm your password.';
    }

    return !this.fullNameError && !this.phoneNumberError && !this.passwordError && !this.confirmPasswordError;
  }

  // ---------- Submit ----------

  onSubmit(): void {
    this.serverError = '';

    if (!this.runAllValidations()) {
      this.cdr.detectChanges();
      return;
    }

    this.isLoading = true;
    this.cdr.detectChanges();

    this.authService.register({
      full_name: this.fullName.trim(),
      phone_number: this.phoneNumber.trim(),
      password: this.password,
      confirm_password: this.confirmPassword
    }).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Registration successful! Redirecting you to login...';
        this.cdr.detectChanges();

        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 2500);
      },
      error: (err) => {
        this.isLoading = false;
        const message = err.error?.error || 'Registration failed. Please try again.';

        // Route the specific "already registered" error to the phone field
        if (message.toLowerCase().includes('already registered')) {
          this.phoneNumberError = message;
        } else {
          this.serverError = message;
        }

        this.cdr.detectChanges();
      }
    });
  }
}