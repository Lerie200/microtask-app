import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

// Uses your local backend during development, and your deployed backend
// once this is hosted. Replace YOUR_DEPLOYED_BACKEND_URL once you have it
// (e.g. https://microtask-backend.onrender.com/api).
const API_URL = window.location.hostname === 'localhost'
  ? 'http://127.0.0.1:5000/api'
  : 'https://YOUR_DEPLOYED_BACKEND_URL/api';

interface RegisterPayload {
  full_name: string;
  phone_number: string;
  password: string;
  confirm_password: string;
}

interface LoginPayload {
  phone_number: string;
  password: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  constructor(private http: HttpClient) {}

  register(payload: RegisterPayload): Observable<any> {
    return this.http.post(`${API_URL}/register`, payload);
  }

  login(payload: LoginPayload): Observable<any> {
    return this.http.post(`${API_URL}/login`, payload).pipe(
      tap((response: any) => {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('is_activated', String(response.user.is_activated));
        localStorage.setItem('full_name', response.user.full_name);
      })
    );
  }

  payActivate(): Observable<any> {
    return this.http.post(`${API_URL}/pay/activate`, {}, { headers: this.authHeaders() });
  }

  getTasks(): Observable<any> {
    return this.http.get(`${API_URL}/tasks`, { headers: this.authHeaders() });
  }

  submitTask(taskId: number, file: File | null, answerText: string | null): Observable<any> {
    const formData = new FormData();
    formData.append('task_id', String(taskId));
    if (file) {
      formData.append('file', file);
    }
    if (answerText) {
      formData.append('answer_text', answerText);
    }
    // Note: don't set Content-Type manually for FormData — the browser
    // sets it automatically with the correct multipart boundary.
    return this.http.post(`${API_URL}/submissions`, formData, { headers: this.authHeaders() });
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('access_token');
  }

  isActivated(): boolean {
    return localStorage.getItem('is_activated') === 'true';
  }

  markActivated(): void {
    localStorage.setItem('is_activated', 'true');
  }

  logout(): void {
    localStorage.clear();
  }

  private authHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }
}