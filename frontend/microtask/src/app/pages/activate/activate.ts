import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/AuthService';

@Component({
  selector: 'app-activate',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './activate.html',
  styleUrl: './activate.css'
})
export class ActivateComponent implements OnInit, OnDestroy {
  status: 'loading' | 'idle' | 'submitting' | 'waiting' | 'error' = 'loading';
  errorMessage = '';
  tillNumber = '';
  amount = 0;
  confirmationMessage = '';

  private pollHandle: any;

  constructor(private authService: AuthService, private router: Router, private cdr: ChangeDetectorRef) {}

  retry(): void {
    if (this.tillNumber) {
      // Payment details already loaded, so just return to the form
      this.status = 'idle';
      this.errorMessage = '';
      this.cdr.detectChanges();
    } else {
      this.status = 'loading';
      this.cdr.detectChanges();
      this.ngOnInit();
    }
  }

  ngOnInit(): void {
    this.authService.getPayInfo().subscribe({
      next: (res) => {
        if (res.is_activated) {
          this.router.navigate(['/tasks']);
          return;
        }
        this.tillNumber = res.till_number;
        this.amount = res.amount;
        this.status = 'idle';
        this.cdr.detectChanges();
      },
      error: () => {
        this.status = 'error';
        this.errorMessage = 'Could not load payment details. Please refresh and try again.';
        this.cdr.detectChanges();
      }
    });
  }

  submitConfirmation(): void {
    if (!this.confirmationMessage.trim()) {
      this.errorMessage = 'Please paste your M-Pesa confirmation message.';
      this.cdr.detectChanges();
      return;
    }

    this.status = 'submitting';
    this.errorMessage = '';
    this.cdr.detectChanges();

    this.authService.submitPaymentConfirmation(this.confirmationMessage.trim()).subscribe({
      next: () => {
        this.status = 'waiting';
        this.cdr.detectChanges();
        // Poll every 5s to check if admin has approved the payment yet
        this.pollHandle = setInterval(() => this.checkActivation(), 5000);
      },
      error: (err) => {
        this.status = 'error';
        this.errorMessage = err.error?.error || 'Could not submit confirmation. Please try again.';
        this.cdr.detectChanges();
      }
    });
  }

  private checkActivation(): void {
    this.authService.getTasks().subscribe({
      next: () => {
        // 200 response means the account is now activated
        clearInterval(this.pollHandle);
        this.authService.markActivated();
        this.router.navigate(['/tasks']);
      },
      error: () => {
        // still pending approval — keep waiting
      }
    });
  }

  ngOnDestroy(): void {
    if (this.pollHandle) {
      clearInterval(this.pollHandle);
    }
  }
}