import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/AuthService';

interface Task {
  id: number;
  task_type: string;
  title: string;
  instructions: string;
  reward_amount: number;
  submission_status: 'pending' | 'approved' | 'rejected' | null;
}

type InputKind = 'photo' | 'audio' | 'choice' | 'number' | 'text';

interface TypeConfig {
  inputKind: InputKind;
  choices?: string[];
  images?: string[];        // reference/option images to display
  playableTone?: boolean;   // whether to show a "Play Sound" button (generated in-browser)
}

// Practice-project placeholder media — stable picsum.photos seeds so images
// don't change on every load. In a real app these would come from the task
// record itself (e.g. a media_url column) rather than being hardcoded here.
const TASK_TYPE_CONFIG: Record<string, TypeConfig> = {
  photo:          { inputKind: 'photo' },
  voice_reading:  { inputKind: 'audio' },
  conversation:   { inputKind: 'audio' },
  audio_choice:   { inputKind: 'choice', choices: ['A dog barking', 'A car engine', 'Someone laughing', 'Rain falling'], playableTone: true },
  image_choice:   { inputKind: 'choice', choices: ['Image A', 'Image B', 'Image C'], images: [
    'https://picsum.photos/seed/matchref/300/200',
    'https://picsum.photos/seed/optionA/150/150',
    'https://picsum.photos/seed/optionB/150/150',
    'https://picsum.photos/seed/optionC/150/150',
  ]},
  categorize:     { inputKind: 'choice', choices: ['Food', 'Animal', 'Vehicle', 'Nature'], images: ['https://picsum.photos/seed/categorize/300/200'] },
  rate_picture:   { inputKind: 'choice', choices: ['Good', 'Bad'], images: ['https://picsum.photos/seed/rateme/300/200'] },
  count_objects:  { inputKind: 'number', images: ['https://picsum.photos/seed/countobjects/300/200'] },
  compare_images: { inputKind: 'text', images: [
    'https://picsum.photos/seed/compareA/220/160',
    'https://picsum.photos/seed/compareB/220/160',
  ]},
};

@Component({
  selector: 'app-tasks',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './tasks.html',
  styleUrl: './tasks.css'
})
export class TasksComponent implements OnInit, OnDestroy {
  tasks: Task[] = [];
  fullName = '';
  isLoading = true;
  errorMessage = '';

  selectedTask: Task | null = null;
  inputKind: InputKind | null = null;
  choices: string[] = [];
  images: string[] = [];
  playableTone = false;

  isSubmitting = false;
  submissionMessage = '';
  textAnswer = '';

  isRecording = false;
  recordedBlob: Blob | null = null;
  recordedUrl: string | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];

  private refreshHandle: any;

  constructor(
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.fullName = localStorage.getItem('full_name') || '';
    this.loadTasks(true);

    // Refresh every 10s so admin approve/reject decisions show up without a manual reload
    this.refreshHandle = setInterval(() => this.loadTasks(false), 10000);
  }

  ngOnDestroy(): void {
    if (this.refreshHandle) {
      clearInterval(this.refreshHandle);
    }
  }

  loadTasks(showSpinner: boolean): void {
    if (showSpinner) {
      this.isLoading = true;
    }

    this.authService.getTasks().subscribe({
      next: (response) => {
        this.tasks = response.tasks;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.isLoading = false;
        this.cdr.detectChanges();
        if (err.status === 403) {
          this.router.navigate(['/activate']);
        } else if (showSpinner) {
          this.errorMessage = 'Could not load tasks. Please log in again.';
        }
      }
    });
  }

  configFor(task: Task): TypeConfig | null {
    return TASK_TYPE_CONFIG[task.task_type] || null;
  }

  isLocked(task: Task): boolean {
    return task.submission_status === 'pending';
  }

  buttonLabel(task: Task): string {
    if (task.submission_status === 'pending') return 'Pending Review';
    return 'Start Task';
  }

  startTask(task: Task): void {
    if (this.isLocked(task)) return;

    const config = this.configFor(task);
    if (!config) return;

    this.selectedTask = task;
    this.inputKind = config.inputKind;
    this.choices = config.choices || [];
    this.images = config.images || [];
    this.playableTone = !!config.playableTone;

    this.submissionMessage = '';
    this.textAnswer = '';
    this.recordedBlob = null;
    this.recordedUrl = null;
    this.isRecording = false;
    this.cdr.detectChanges();
  }

  cancelTask(): void {
    this.selectedTask = null;
    this.inputKind = null;
    this.submissionMessage = '';
    this.stopRecordingStream();
    this.cdr.detectChanges();
  }

  // ---------- Photo ----------
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0 || !this.selectedTask) return;
    this.doSubmit(input.files[0], null);
  }

  // ---------- Generated tone for "listen and choose" ----------
  playTone(): void {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(440, ctx.currentTime);
    oscillator.connect(gain);
    gain.connect(ctx.destination);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    oscillator.start();
    oscillator.stop(ctx.currentTime + 0.6);
  }

  // ---------- Audio recording (voice_reading / conversation) ----------
  async startRecording(): Promise<void> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioChunks = [];
      this.mediaRecorder = new MediaRecorder(stream);

      this.mediaRecorder.ondataavailable = (e) => this.audioChunks.push(e.data);
      this.mediaRecorder.onstop = () => {
        this.recordedBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        this.recordedUrl = URL.createObjectURL(this.recordedBlob);
        this.cdr.detectChanges();
      };

      this.mediaRecorder.start();
      this.isRecording = true;
      this.cdr.detectChanges();
    } catch (err) {
      this.submissionMessage = 'Microphone access denied or unavailable.';
      this.cdr.detectChanges();
    }
  }

  stopRecording(): void {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
      this.cdr.detectChanges();
    }
  }

  private stopRecordingStream(): void {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    this.isRecording = false;
  }

  submitRecording(): void {
    if (!this.recordedBlob) return;
    const file = new File([this.recordedBlob], `recording_${Date.now()}.webm`, { type: 'audio/webm' });
    this.doSubmit(file, null);
  }

  // ---------- Choice / number / text ----------
  submitChoice(choice: string): void {
    this.doSubmit(null, choice);
  }

  submitTextAnswer(): void {
    if (!this.textAnswer.trim()) return;
    this.doSubmit(null, this.textAnswer.trim());
  }

  // ---------- Shared submit logic ----------
  private doSubmit(file: File | null, answerText: string | null): void {
    if (!this.selectedTask) return;
    const taskId = this.selectedTask.id;

    this.isSubmitting = true;
    this.cdr.detectChanges();

    this.authService.submitTask(taskId, file, answerText).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.submissionMessage = 'Submitted! Awaiting review.';

        // Optimistically lock the button immediately, without waiting for the next poll
        const task = this.tasks.find(t => t.id === taskId);
        if (task) task.submission_status = 'pending';

        this.cdr.detectChanges();
      },
      error: (err) => {
        this.isSubmitting = false;
        this.submissionMessage = err.error?.error || 'Submission failed. Please try again.';
        this.cdr.detectChanges();
      }
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}