import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/AuthService';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent {
  phoneNumber = '';
  password = '';

  phoneNumberError = '';
  passwordError = '';
  serverError = '';
  successMessage = '';

  isLoading = false;

  private readonly PHONE_REGEX = /^0\d{9}$/;

  constructor(
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  validatePhoneNumber(): void {
    this.serverError = '';
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
    this.serverError = '';
    if (!this.password) {
      this.passwordError = '';
    } else {
      this.passwordError = '';
    }
  }

  private runAllValidations(): boolean {
    this.validatePhoneNumber();

    if (!this.phoneNumber.trim()) this.phoneNumberError = 'Phone number is required.';
    if (!this.password) this.passwordError = 'Password is required.';

    return !this.phoneNumberError && !this.passwordError;
  }

  onSubmit(): void {
    this.serverError = '';

    if (!this.runAllValidations()) {
      this.cdr.detectChanges();
      return;
    }

    this.isLoading = true;
    this.cdr.detectChanges();

    this.authService.login({
      phone_number: this.phoneNumber.trim(),
      password: this.password
    }).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.successMessage = 'Login successful! Redirecting...';
        this.cdr.detectChanges();

        setTimeout(() => {
          if (response.user.is_activated) {
            this.router.navigate(['/tasks']);
          } else {
            this.router.navigate(['/activate']);
          }
        }, 1500);
      },
      error: (err) => {
        this.isLoading = false;
        const message = err.error?.error || 'Login failed. Please try again.';

        if (err.status === 404) {
          // Phone number not registered
          this.phoneNumberError = message;
        } else if (err.status === 401) {
          // Wrong password
          this.passwordError = message;
        } else {
          this.serverError = message;
        }

        this.cdr.detectChanges();
      }
    });
  }
}