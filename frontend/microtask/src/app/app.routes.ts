
import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home';
import { RegisterComponent } from './pages/register/register';
import { LoginComponent } from './pages/login/login';
import { ActivateComponent } from './pages/activate/activate';
import { TasksComponent } from './pages/tasks/tasks';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'login', component: LoginComponent },
  { path: 'activate', component: ActivateComponent },
  { path: 'tasks', component: TasksComponent },
];