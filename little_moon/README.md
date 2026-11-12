# Little Moon — CBSE Classes 1–8

Little Moon is a separate Streamlit learning app for CBSE learners in Classes 1–8, created by **NilanjanC**. Students choose their class, subject, and a suggested chapter, or type a chapter/topic from their own school's syllabus. It includes key words, fresh multiple-choice practice with explanations, custom-mark timed question papers, PDF downloads, fun facts, and a Razorpay donation form.

The subject and chapter suggestions are broad CBSE/NCERT-aligned examples. Schools may use different textbooks, language combinations, or chapter titles, so students can enter their own chapter. English and Bengali are the language subjects offered in this app; generated learning material is otherwise in English. These suggestions are not a substitute for a school's current syllabus.

## Run locally

1. Install Python 3.12.
2. From this folder, create and activate a virtual environment: `python -m venv .venv` then `.venv\\Scripts\\Activate.ps1` (Windows) or `source .venv/bin/activate` (macOS/Linux).
3. Install dependencies: `pip install -r requirements.txt`.
4. Create `.streamlit/secrets.toml` with `GEMINI_API_KEY = "your-key"` (or set the environment variable).
5. Run `streamlit run app.py`.

Keep the real Gemini key private; add it in Streamlit Cloud's app secrets when deploying. The shared project root already specifies Python 3.12 and the required packages.

## Deploy as a separate Streamlit app

In Streamlit Community Cloud, create a new app using the `75neel-ops/little-sun` repository, `main` branch, and **`little_moon/app.py`** as the main file. Add `GEMINI_API_KEY` under the new app's Secrets. This creates an independent Little Moon deployment, separate from Little Sun.

After Streamlit gives the new app its public URL, put that URL in the `src` of the iframe in the Little Moon install page at `https://github.com/75neel-ops/deepbluemonkey/tree/main/little-moon`. The install page uses the moon icon and app name **Little Moon** for desktop and mobile installation.

## Questions and repetition

Questions are generated for the selected class, subject, and topic with `gemini-3.5-flash-lite`. Repeats are filtered within the current browser session and activity. Without a shared database, the app cannot guarantee questions never repeat across different students or later visits.

## Razorpay donations

The donation form uses the Razorpay payment button ID supplied by the owner. The app embeds only the public button ID; never add a Razorpay secret key to the repository.

## Curriculum references

- [NCERT textbooks and Grades I–VIII catalogue](https://ncert.nic.in/textbook.php)
- [NCERT Bridge Programme for Grades 1, 3, 5, 6 and 8](https://ncert.nic.in/bridge_programme.php)
- [CBSE 2026–27 curriculum portal](https://cbseacademic.nic.in/curriculum_2027.html) (secondary and senior secondary)

