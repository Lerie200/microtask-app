import { Component, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../services/AuthService';
@Component({
  selector: 'app-activate',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './activate.html',
  styleUrl: './activate.css'
})
export class ActivateComponent implements OnDestroy {
  status: 'idle' | 'waiting' | 'error' = 'idle';
  errorMessage = '';
  private pollHandle: any;

  constructor(private authService: AuthService, private router: Router, private cdr: ChangeDetectorRef) {}

  payNow(): void {
    this.status = 'waiting';
    this.errorMessage = '';
    this.cdr.detectChanges();

    this.authService.payActivate().subscribe({
      next: () => {
        // STK push accepted — now poll /api/tasks every 4s;
        // once it stops returning 403, the account is activated.
        this.pollHandle = setInterval(() => this.checkActivation(), 4000);
      },
      error: (err) => {
        this.status = 'error';
        this.errorMessage = err.error?.error || 'Could not start payment. Please try again.';
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
        // still 403 — keep waiting, do nothing
      }
    });
  }

  ngOnDestroy(): void {
    if (this.pollHandle) {
      clearInterval(this.pollHandle);
    }
  }
}