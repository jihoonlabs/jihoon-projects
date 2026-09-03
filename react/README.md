JIHOON-PROJECTS
A modern web application built with Next.js App Router, TypeScript, and SCSS modules. This repository houses feature-based integrations and core UI components.

Tech Stack
Framework: Next.js (App Router)

Language: TypeScript

State Management: Zustand

Styling: SCSS Modules

Package Manager: pnpm

Getting Started
Prerequisites
Ensure you have Node.js and pnpm installed on your machine.

Quick Start
Run the following commands in order to set up and run the development environment:

Install Dependencies

Command: pnpm install

Approve Build Scripts (If prompted by security policy)

Command: pnpm approve-builds

Run Development Server

Command: pnpm dev

Open http://localhost:3000 in your browser to view the application.

Available Scripts
pnpm dev — Starts the local development server at localhost:3000

pnpm build — Builds the application for production

pnpm start — Starts the production server after building

pnpm lint — Runs ESLint to check for code quality issues

Project Structure
react/
├── public/               # Publicly accessible static assets
└── src/
├── app/              # App Router routes and page components
│   └── (auth)/       # Authenticated route group
│       └── login/    # Login page component
├── assets/           # Module-bundled, build-optimized static assets
├── components/       # Reusable UI components
└── store/            # Global Zustand state stores

Development Workflow
This repository follows a feature-branch workflow:

main — Stable production codebase

feature/* — Feature development and active experiments (e.g., feature/dashboard)

License
This project is maintained for internal development and learning purposes.