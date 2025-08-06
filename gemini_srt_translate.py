import os
import srt
import google.generativeai as genai
import time
import argparse

# ========== Set Gemini API Key ==========
API_KEY = "YOUR_API_KEY"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ========== Translation Function ==========
def translate_text(text, target_lang):
    prompt = (
        f"Please translate all the captions below into {target_lang}, only output the translated content, and the order should be consistent with the original text. Each timestamp's content should be replaced with the {target_lang} translation, and no other content should be added to ensure the accuracy of the timeline. Pay attention to the translation of proper nouns and names to ensure accuracy. Try to align the proper tone and style with the original text. If the original text is in a specific format, please maintain that format in the translation.\n\n"
        f"Do not add any explanations, formats, or unnecessary content, just output the translated subtitle text, with each line corresponding to the original subtitle line:\n\n{text}"
    )
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            import traceback
            print(f"[!] NO.{attempt+1} translation failed: {e}")
            traceback.print_exc()
            time.sleep(5) 
    return "[Translation failed after 3 attempts]"

# ========== Main Translation Process ==========
def translate_srt(input_file, output_file, target_lang):
    with open(input_file, "r", encoding="utf-8") as f:
        srt_content = f.read()

    subtitles = list(srt.parse(srt_content))
    translated_subs = []
    batch_size = 10  # Translate 10 subtitles at a time

    for i in range(0, len(subtitles), batch_size):
        print(f"Now translating batch {i // batch_size + 1} of {len(subtitles) // batch_size + 1}...")
        batch = subtitles[i:i+batch_size]
        batch_text = "\n".join(sub.content for sub in batch)
        translated = translate_text(batch_text, target_lang)

        translated_lines = translated.strip().split("\n")
        for j, sub in enumerate(batch):
            if j < len(translated_lines):
                sub.content = translated_lines[j]
            translated_subs.append(sub)
        time.sleep(10) 
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(srt.compose(translated_subs))

    print(f"Translation completed and saved to: {output_file}")

# ========== Command Line Interface ==========
def main():
    parser = argparse.ArgumentParser(description="Translate SRT files using Gemini API")
    parser.add_argument("--input_file", required=True, help="Path to the input SRT file")
    parser.add_argument("--output_file", required=True, help="Path to the output SRT file")
    parser.add_argument("--target_lang", default="zh", help="Target language for translation (default: 'zh')")
    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output_file
    target_lang = args.target_lang
    translate_srt(input_file, output_file, target_lang)

if __name__ == "__main__":
    main()
