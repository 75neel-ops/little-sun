# Little Sun — ICSE Classes 1–8

**Little Sun** is a friendly Streamlit learning app for ICSE/CISCE learners in Classes 1–8, created by **NilanjanC**. Students choose a class, subject, and chapter from a suggested list, or type a custom chapter if their school syllabus differs. It offers chapter keywords, fresh multiple-choice practice with explanations, timed custom-mark question papers, PDF downloads, and fun facts. Bengali is used for the Bengali subject; the other subjects use English.

The subject and chapter suggestions follow a broad CISCE primary and upper-primary progression: Classes I–II include Environmental Studies; III–V include Science and Social Studies; VI–VIII separate Physics, Chemistry, Biology, History, Civics, and Geography. School chapter names and subject offerings vary, so the custom chapter field accepts the wording in a student's own textbook. These are topic suggestions, not an official school syllabus or past-paper archive.

## Run locally

1. Install Python 3.12.
2. In this folder, create and activate a virtual environment: `python -m venv .venv` then `.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate` (macOS/Linux).
3. Install dependencies: `pip install -r requirements.txt`.
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace the placeholder with your Gemini API key.
5. Start the app: `streamlit run app.py`.

```toml
GEMINI_API_KEY = "your-key"
```

Keep `.streamlit/secrets.toml` private. The example file is safe to commit; your real key is ignored by Git.

## Publish with GitHub and Streamlit Community Cloud

1. Create a GitHub repository and push this project. If this workspace is already connected to the repository, commit and push the files in the normal way.
2. In Streamlit Community Cloud, choose **Create app**, select the repository and branch, and set the main file to `app.py`.
3. Add `GEMINI_API_KEY = "your-key"` under the app's **Settings → Secrets**. Choose Python 3.12 if asked; `runtime.txt` also specifies it.
4. Deploy. The live app URL can be shared with students; no API key is exposed in the browser.

## Question freshness

Questions are generated for the selected class, subject, and topic using `gemini-3.5-flash-lite`. Little Sun avoids repeating question text within the same browser session and learning activity. Without a shared database, it cannot guarantee that a question will never appear in another student's session or a later visit. Streamlit Community Cloud does not provide durable shared storage by default.

## PDF papers

After submitting a timed paper, students can download a PDF with the paper and answer explanations, and a separate blank paper to print. The countdown runs while the paper is open; the page refreshes the displayed time automatically.

## Desktop icon

On desktop Chrome or Edge, open the deployed app and select **Install** in the address bar (the install control is visible in the supplied screenshot), or use the browser menu to create a shortcut. This adds Little Sun to the desktop/apps list with its sun icon. On phones, use the browser's **Add to Home Screen** option.

## Donations

The sidebar's **Donate with Razorpay** button opens the payment form in a large, scrollable popup. It uses the public payment button ID supplied by the owner. The button is managed through Razorpay; never add a Razorpay secret key to this repository.

## GitHub safety

Never place the actual Gemini key in source code, README files, or a committed `secrets.toml`. Add it as a Streamlit Cloud secret instead. The `.gitignore` excludes the local secrets file.

## Sources

- [CISCE Primary Curriculum](https://cisce.org/wp-content/uploads/2025/03/PrimaryCurriculum.pdf)
- [CISCE Preschool to Class VIII curriculum](https://cisce.org/wp-content/uploads/2025/03/PreSchoolCurriculum2.pdf)
- [Gemini 3.5 Flash-Lite API model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)

