import re

with open(r"c:\qaforge-v5\frontend\css\app.css", "r", encoding="utf-8") as f:
    css = f.read()

def scale_rem(match):
    val = float(match.group(1))
    new_val = round(val * 1.3, 2)
    return f"{new_val}rem"

# Scale .Xrem and X.Xrem
css = re.sub(r"(\d*\.\d+|\d+)rem", scale_rem, css)

# Make transitions smoother
css = css.replace("transition:all .2s", "transition:all .3s ease")
css = css.replace("transition:all .18s", "transition:all .3s ease")
css = css.replace("transition:all .15s", "transition:all .3s ease")

with open(r"c:\qaforge-v5\frontend\css\app.css", "w", encoding="utf-8") as f:
    f.write(css)

print("Scaled CSS successfully!")
