# Cover images for manual upload

Each file is named exactly after the blog post it belongs to. Upload them by
hand in the Selldone backoffice (Blog → the post → cover image).

Why manual: Selldone's API has no update endpoint. The only programmatic way to
change a published article is to delete and recreate it, which changes its ID.
Uploading through the backoffice avoids that entirely.

Generated with Gemini (Nano Banana) via `scripts/gen_cover.py`, 16:9,
TokyLabs magenta #FF0082 on off-white line art.

| Post | Article ID |
|---|---|
| Why a Student Hackathon Is One of the Best Learning Experiences You Can Give Your Child | 745683 |
| What Happens to a Child's Brain When They Build a Robot — And Why It Matters More Than You Think | 744993 |
| Why Schools Can't Find Enough Robotics Teachers — And What That Means for Educators | 744797 |
| In the Age of AI, Effort Is Your Child's Most Valuable Skill | 744544 |
| Why the Flipped Classroom Is the Future of Robotics Education | 744103 |
| When Creativity Meets Responsibility: How Upcycling Projects Turn Kids Into Thoughtful Makers | 743879 |
| The Tiniest Robots in the World — And What They Teach Our Kids About Possibility | 743718 |
| Why Critical Thinking Is the Most Important Skill You Can Give Your Child in the Age of AI | 743623 |
| Why Creativity Is the Superpower Every Child Needs in the Age of AI | 743479 |
| Inside a TokyLabs MakerSpace Session: 7 Moments That Change How Kids Think | 747095 |
| Curiosity Today, Career Tomorrow: 5 STEM Paths Your Child Can Start Exploring Now | 748078 |

Note: three of these posts (744993, 744797, 743718) already have older Canva
covers pointing at per-session git branches. Replacing them with these files
also removes that dependency.
