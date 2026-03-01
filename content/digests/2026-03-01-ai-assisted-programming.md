---
config: AI-Assisted Programming
date: '2026-03-01T13:35:58.509345'
model: deepseek-chat
sources_analyzed: 44
title: AI-Assisted Programming Digest
total_tokens: 8595
---

<main>
    <h2>THIS WEEK'S BIG PICTURE</h2>
    <p>The narrative this week solidifies a major shift: coding agents are now considered a practical, reliable part of the development workflow. Multiple sources, from detailed case studies to high-profile project migrations, confirm that the quality and tenacity of models since late 2025 have crossed a threshold. This is leading to the formalization of "Agentic Engineering" as a discipline, with best practices emerging around test-driven development, managing cognitive debt, and structuring multi-agent workflows. Concurrently, major platform integrations (OpenAI with AWS, GitHub Copilot's new features) are making these powerful tools more accessible and integrated into existing developer environments.</p>

    <h2>TOP 3 TOOLS/TECHNIQUES TO KNOW</h2>
    <ul>
        <li>
            <h3><a href="https://simonwillison.net/guides/agentic-engineering-patterns/">Agentic Engineering Patterns</a></h3>
            <p><strong>What it is:</strong> A growing guide documenting practical patterns and practices for building software with AI coding agents.</p>
            <p><strong>Why it matters:</strong> It moves beyond hype to provide concrete, actionable advice for developers to get reliable results, such as enforcing red/green TDD and writing linear walkthroughs to manage complexity.</p>
            <p><strong>Key detail:</strong> The guide explicitly frames its advice around the new economic reality that <em>writing code is cheap now</em>, challenging traditional engineering habits focused on minimizing code production.</p>
        </li>
        <li>
            <h3><a href="https://github.blog/ai-and-ml/github-copilot/whats-new-with-github-copilot-coding-agent/">What’s new with GitHub Copilot coding agent</a></h3>
            <p><strong>What it is:</strong> A significant update to GitHub's Copilot coding agent with several new professional features.</p>
            <p><strong>Why it matters:</strong> It adds crucial controls and integrations like a model picker, self-review, built-in security scanning, and CLI handoff, making the agent more versatile and integrated into a full development cycle.</p>
            <p><strong>Key detail:</strong> The addition of custom agents allows teams to tailor the AI's behavior and knowledge to specific codebases or tasks, moving from a general-purpose tool to a specialized team member.</p>
        </li>
        <li>
            <h3><a href="https://code.claude.com/docs/en/remote-control">Claude Code Remote Control</a></h3>
            <p><strong>What it is:</strong> A new Claude Code feature that lets you run a session on your local machine and control it from web or mobile interfaces.</p>
            <p><strong>Why it matters:</strong> It decouples the AI's processing environment from the interface, allowing you to start a long-running coding task on a powerful machine and monitor or direct it from anywhere.</p>
            <p><strong>Key detail:</strong> The feature is currently described as "a little bit janky" and may require account permissions, indicating it's an early but powerful step towards more flexible agent deployment.</p>
        </li>
    </ul>

    <h2>CODE & WORKFLOW UPDATES</h2>

    <h3>MODELS & APIs</h3>
    <p><strong><a href="https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified">Why we no longer evaluate SWE-bench Verified</a></strong><br>
    OpenAI has deprecated the SWE-bench Verified benchmark for evaluating coding models, citing test contamination and flawed measurements. They state it mismeasures true progress and now recommend the newer SWE-bench Pro benchmark instead.
    </p>

    <h3>TOOLS & INTEGRATIONS</h3>
    <p><strong><a href="https://github.blog/ai-and-ml/github-copilot/from-idea-to-pull-request-a-practical-guide-to-building-with-github-copilot-cli/">From idea to pull request: A practical guide to building with GitHub Copilot CLI</a></strong><br>
    A new hands-on guide details the workflow for using GitHub Copilot CLI to go from a natural language prompt to a reviewable pull request. It focuses on the practical flow from terminal to IDE to GitHub, emphasizing the CLI as a starting point for agentic work.
    </p>

    <h3>PRACTICAL WORKFLOWS</h3>
    <p><strong><a href="https://simonwillison.net/guides/agentic-engineering-patterns/first-run-the-tests/">First run the tests</a></strong><br>
    This pattern argues that automated tests are now non-negotiable when working with AI coding agents, as they provide a fast, objective feedback loop to verify correctness. It works best at the start of any new agentic task to establish a baseline and prevent the accumulation of "cognitive debt" from poorly understood AI-generated code.
    </p>

    <h2>QUICK LINKS</h2>
    <ul>
        <li><a href="https://minimaxir.com/2026/02/ai-agent-coding/">An AI agent coding skeptic tries AI agent coding, in excessive detail</a> – A compelling, detailed personal account of a skeptic being converted by the practical capabilities of modern coding agents.</li>
        <li><a href="https://ladybird.org/posts/adopting-rust/">Ladybird adopts Rust, with help from AI</a> – A serious case study of using AI agents to assist in a large-scale, critical language port for a browser project.</li>
        <li><a href="https://blog.timcappalli.me/p/passkeys-prf-warning/">Please, please, please stop using passkeys for encrypting user data</a> – A critical security warning for developers about the risks of using passkey-derived keys for encryption, as users lose access permanently.</li>
    </ul>
</main>