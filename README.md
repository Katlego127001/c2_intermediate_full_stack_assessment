# c2_intermediate_full_stack_assessment# Full Stack Intermediate Assessment

## Project: Internal Job Tracking System

Build a full stack web application that allows a company to manage internal job requests, create employees, assign work to employees, and track progress.

---

# Core Requirements

## Tech-stack

- **Frontend:** React (preferably with NextJs)
- **Backend:** Python (preferably FastApi)
- **Database:** SQL (preferably PostgresSql)

## 1. Authentication

Users must be able to:

- Register
- Login
- Logout

### Roles

The system must support:

- Admin
- Employee

# 2. Dashboard

After login:

## Admin Dashboard

Should display:

- Total jobs
- Completed jobs
- Total employees

# 3. Job Management

Admins must be able to:

- Create jobs
- Edit jobs
- Delete jobs
- Assign jobs to employees

Each job must contain:

- Title
- Description
- Priority
- Status
- Due date
- Assigned employee
- Created date

---

# 4. Job Status Workflow

Jobs should support the following statuses:

- In Progress
- Completed

Employees should only be able to update:

- Status

---

# 5. Employee Management

Admins must be able to:

- Create employees
- Edit employee information
- Deactivate employees

Each employee should contain:

- First name
- Last name
- Email address
- Phone number
- Role
- Department
- Employment status
- Created date

## Employment Statuses

- Active
- Inactive

## Employee Features

### Admin Features

Admins should also be able to:

- Assign jobs to employees
- View employee workload
- Search employees by name or department
- Filter employees by role or status

### Employee Features

Employees should be able to:

- View Jobs
- View their own profile
- Update limited profile information:
  - Phone number
  - Password

---

## Submission Guidelines

1. Fork this project to your GitHub profile, make the fork public, and clone it onto your laptop.
2. Once you have completed building and testing the app, push your changes to your public fork and email the repository link to craig.barsdorff@c2grouptech.co.za.
3. Include a **README.md** explaining how to run the project and any special notes you want to make us aware of.
4. **If the project cannot run on our side, unfortunately then we will not be able to evaluate it properly - so it is improtant that your app works.**

---

## Contact

For any questions, reach out to thulaganyo.mooki@c2grouptech.co.za or craig.barsdorff@c2grouptech.co.za.
