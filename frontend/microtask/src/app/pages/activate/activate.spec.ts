import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Activate } from './activate';

describe('Activate', () => {
  let component: Activate;
  let fixture: ComponentFixture<Activate>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Activate],
    }).compileComponents();

    fixture = TestBed.createComponent(Activate);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
