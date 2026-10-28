from pathlib import Path

from extractor import extract_text
from analyzer import analyze_job_description


def main():
    file_path = input(
        "Enter the path of your JD PDF/DOCX file: "
    ).strip().strip('"')

    path = Path(file_path)

    if not path.is_file():
        print("Error: File not found.")
        return

    try:
        content = path.read_bytes()

        jd_text = extract_text(path.name, content)

        print("\nAnalyzing job description...\n")

        result = analyze_job_description(jd_text)

        print(result.model_dump_json(indent=2))

    except Exception as exc:
        print(f"Analysis failed: {exc}")


if __name__ == "__main__":
    main()