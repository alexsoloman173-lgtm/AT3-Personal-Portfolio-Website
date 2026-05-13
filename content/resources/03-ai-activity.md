---
id: 3
title: AI Activity
slug: ai-activity
modal_title: Resource 3: AI Activity (Week 8)
icon: sparkles
summary: A study of LLM-generated lesson plans.
image: resources/lesson_plan.png
image_alt: AI Task lesson plan thumbnail
media_image: resources/lesson_plan.png
media_downloads: resources/Lesson%20Planning%20Is%20Not%20a%20Prompting%20Problem.pdf, resources/Introducing%20Linear%20Equations%20%28one-shot%29.pdf, resources/Introducing%20Linear%20Equations%20%28with%20harness%29.pdf
media_download_names: Lesson Planning Is Not a Prompting Problem, Introducing Linear Equations (one-shot), Introducing Linear Equations (with harness)
card_class: wide
count_id: ref3Count
countable: true
---

Developing this resource was both fun and interesting. As an expert in software development and a close follower of deep learning applications, I came in with pretty serious advantages. It also happens that I built a lesson plan generator in week 2 of the course - integrated into my slide authoring tool SlideKey (see the resource for more information) - just for fun! So I'd already learned quite a lot about how to apply LLMs to this specific task, and had a battle-tested architecture ready to go.

Thus, my approach was just to rebuild it, with an LLM-coding agent, with a minimum of prompts. I then asked the agent to write a blog post - from its own perspective and in its own words - analyzing the problem space, describing our solution, and comparing the outputs of our "harness" versus "one-shot" prompt. I have to say: reading the agent's post was delightful.

The result is far from perfect, and the artifact that it ultimately generated could use a lot more work. But for 10 prompts - plus an 11th for the blog post - I am pleased with the result. Start by reading the download called "Lesson Planning is Not a Prompting Problem", and then look at the one-shot and harness versions of the lesson plan.

To answer the process questions directly: this was definitely not my first use of an LLM; I came into the task with prior experience building a lesson-plan generator, which shaped how I framed the prompting work. The main factors I considered were curriculum alignment, learner appropriateness, specificity of lesson structure, and output reliability: all areas where I already knew were problematic for a one-shot prompting approach. In practical terms, I harnessed the model toward concrete planning moves - clear learning intentions, worked examples, checks for understanding, and sequencing that matched an introductory linear equations lesson.

I was still surprised in a few places. The model could produce polished-sounding pedagogical language quickly, but it could also drift into useless filler or thin instructional logic if left under-constrained, which reinforced the value of the harness approach over one-shot prompting. So yes, I was satisfied overall, but conditionally: satisfied with the speed of ideation and baseline structure, not fully satisfied that it would survive contact with an actual classroom. The strengths were pace, coherence, and useful draft scaffolding; the weaknesses were uneven differentiation, occasional vagueness, and the need for substantial teacher judgment before classroom use.

And just in case you want to see a demonstration, this video (sorry it's 40 minutes long) actually demonstrates the whole activity in a conversational style.

## Video Walkthrough

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
	<iframe
		src="https://www.youtube.com/embed/OEIR847CIpE?rel=0&modestbranding=1"
		title="AI Activity Video"
		style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
		allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
		allowfullscreen>
	</iframe>
</div>

If the embedded player is blocked in your browser, open the video directly here: [Watch on YouTube](https://youtu.be/OEIR847CIpE).