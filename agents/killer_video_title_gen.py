"""
This script generates killer video titles for YouTube videos using OpenAI's API.
"""

import os
import sys
import json

from dotenv import load_dotenv
from openai import OpenAI

try:
    from .utils import try_to_load_json
    from .persona_testing import PersonaTester
except ImportError:
    from utils import try_to_load_json
    from persona_testing import PersonaTester

load_dotenv()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o3-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE,
)


def gen_video_titles(videos_string: str, num_of_titles: int) -> str:
    """
    Take the description (videos_string) of the existing YouTuber videos
    and generate a brief summary about their style.
    """
    prompt = f"""
    You are a World wide known Youtuber, even bigger than MR Beast, and you are a master of creating killer video titles.
    Your objective is to generate {str(num_of_titles)} perfects videos titles for this video.
    Here are some guidelines for title generation
    <guidelines>
        Especially at higher levels of YouTube, they stress me out all the time. But I was reviewing some videos shared to this subreddit and I noticed that the vast majority of small creators just completely have the wrong ideas when it comes to titles. And this isn't a roast, it's hard to know where to start with titles, especially if you have no guidance. So here's some guidance.
        I originally shared this advice to someone individually but I thought it could help the rest of the community.
        Titles should be short. Generally 50 characters or less is a safe bet. Mostly this is because in some places titles longer than this will be cut off and the viewer won't see the full title. But also, short titles are easier to see and immediately understand. And if you can come up with a way to describe your video in 50 characters or less, that probably means it's a strong idea. (and the other way around. If you can't think of a short, simple title for your video, that potentially means your idea is not that clear/strong).
        Titles should be not only short, but also simple. They should use simple language that people of all ages and education levels can understand. Anytime your video is shown, it's competing with hundreds of other videos on the screen at any given time. You want a bold, easy to understand title that will catch someone's eyes. Overly long, complex titles don't stand out, they are easy to glaze over because we actually have to "think" about what they say, and no one wants to do that. Consider these two titles.
        A. One Hit Kills? Full Overwatch Review and Gameplay | Sam the Gamer
        B. Overwatch is a Terrible Game
        One of these requires significantly more effort to read and understand than the other. We want to be more like the second one. Not only is it easier to read, it much more clearly communicates what to expect from the video.
        Title should not be vague**.** This is a big one I've been seeing a lot. People understand that you have to generate curiosity in your titles so they make them super vague. But vagueness causes confusion, not curiosity. Consider these two title:
        A. Before You Start Cycling, Do This
        B. Everything You Need to Know as a New Cyclist
        Title A is okay, but it's a bit unclear what to expect from the video. Title B however is extremely clear in showing us what the video is about.
        An easy way to think of your title is "A simple statement that, alongside my thumbnail, shows why my video is worth watching". What is special about your video? Why should people watch it? What is contained in the video that people need to see? The answer to that should most likely be in the title (and thumbnail). Sometimes the idea itself is so interesting, you can just put the premise of the video as the title. Like if you have a video about climbing mount everest, you could probably just title the video "I Climbed Mount Everest" because that's interesting alone. Most top YouTubers have figured out how to do this every video.
        If you're doing a Overwatch gameplay, you probably wont get way with "Overwatch Gameplay" as the title because that's not that interesting. So then the question is, what IS interesting about the video? As implied before, this is a good way to know if you actually have a good video idea--if you can't figure out what's interesting you might not. So maybe Sam the Gamer became the top ranked player in Overwatch - so he made a video about it -- THAT'S interesting. So maybe a good title is "I Got Rank 1 in Overwatch"
        Im sure you've seen successful videos that break these rules and any other titles advice you've received, but that's how it goes. Titles are just one part of the picture. Sometimes the other parts are so strong it makes up for it.
        
        More info:
        YouTube isn’t just another social media platform like TikTok or Instagram. It is a search engine, like Google, specifically for video content.
        This means people actively search for content they’re interested in, and your YouTube title is the gateway to users discovering your videos.
        A YouTube title greatly influences search engine optimization (SEO) and video ranking.
        YouTube’s algorithm scans your titles for specific keywords and phrases and bumps your video higher in search results because of it.
        How To Write YouTube Video Titles In 7 Easy Steps
        Creating an effective YouTube Video Title isn’t always an easy task. There’s a lot of strategy and technique involved.
        Follow these 7 easy steps to create a YouTube video title that increases views.
        Use Simple And Clear Language
        Create a title using elementary language that is relatively conversational.. Simplify your title to a 5th-grade reading level, making it easier to read and understand.
        Simple YouTube video description from Finn Whitaker
        YouTube
        While we don’t necessarily recommend using one word to describe your video like this YouTube creator. Sometimes all you need is a short and concise title to get your point across.
        The only exception: know your audience. If you are creating a video for a niche community that uses more advanced language, then you can use a more specific video title.
        Optimize Title Length And Format
        YouTube limits titles to 100 characters; however, long titles get cut off at a certain point.
        Keep your YouTube video title between 60 and 70 characters for full visibility on both desktop and mobile.
        Alex Armitage grabbing audience's attention with his YouTube video title
        YouTube
        The words up front grab the viewer’s attention. People have a low attention span, so get your point across at the beginning of the title.
        In this example, the second title, “Grocery Shopping Tips – Daily Vlog #30,” is better because it puts the main keywords first, making the content clearer and more attractive to viewers.
        Use title modifiers such as “How-to,” “Top 10,” or “Ultimate Guide” to gain more viewership. These are small things that can go a long way.
        YouTube Video Title Ideas: using "Top 15," strategy to gain more viewership
        Youtube
        Be Honest And Direct
        Avoid clickbait titles. Don’t trick viewers into watching the video.
        If your content isn’t giving them what they want, then they will click off your video immediately.
        As a result, your average watch time will decrease, and the algorithm will show your video to fewer people.
        On the other hand, if your average watch time increases, so will your views. So, be honest about the content of your video in your title, even if you get fewer views right away.
        Get Inspiration From Competitors
        Search your topic on YouTube and scroll through the top videos.
        Look for videos with lots of views but not many subscribers. This means the video is doing well, and YouTube is promoting this video.
        YouTube Video Title Ideas: get inspiration from successful vidoes
        YouTube
        Get inspiration from these videos. Look at the wording and structure of their titles, and incorporate them into your video titles.
        Conduct Keyword Research
        Keyword research
        The process of identifying words and phrases that rank well in search engines such as Google and YouTube
        Keywords should be included in not only your video title, but also the description, thumbnail, and tags.
        “top travel destinations 2024” YouTube search, Ryan Shirley's video is one of the top results
        YouTube
        When searching for “top travel destinations 2024”, this creator’s video is one of the top results. This is partly because he uses keywords like “2024”, “travel”, and “travel guide”.
        However, finding the right keywords can be difficult.
        Use keyword research tools like Ahrefs. This software suggests relevant keywords in your title to help it rank higher in search results.
        Ahrefs - keyword research tool
        Ahrefs
        Try our new YouTube Channel Keyword Generator today!
        Add Hashtags To Your Video Titles
        Hashtags allow YouTube to understand your content and target a specific audience.
        If YouTube understands your content it will categorize it and show it to an audience that is interested in similar content.
        Hashtags will also allow viewers to find these videos on the hashtag page.
        YouTube Video Title Ideas: adding Hashtags To Your Video Titles
        YouTube
        How do I add hashtags to my YouTube videos?
        At the bottom of your video’s description, add the # symbol and start typing words or keywords related to your topic. YouTube will give hashtag suggestions and choose which ones work best.
        Utilize Title Analyzer Tools
        Once you create your title, how do you know if it’s effective for YouTube SEO?
        Use Headline Studio’s Analyzer Tool to not only give you feedback on SEO rankings but also generate alternative YouTube video titles for you.
        Headline Studio’s Analyzer Too
        What Is A YouTube Video Title Generator?
        What if we told you it was possible to create an effective YouTube title in the blink of an eye?
        Headline Studio’s YouTube title generator creates multiple titles at once so that you can choose the best title for your video. one for you.
        It analyzes your titles, gives suggestions, and scores its SEO ranking compared to the competition.
        Headline Studio’s Analyzer Too
        Recommended reading:
        73 Easy Ways To Write A Headline That Will Reach Your Readers
        SEO Headlines: 5 Simple Ways to Rank on SERPs
        50+ Headline Formulas and Templates To Craft A Perfect Headline
        40 YouTube Video Title Ideas
        How-To And Tutorial Videos
        “How to [Achieve Desired Outcome] in [Specific Time Frame]”
        “Step-by-Step Guide: [Process or Skill]”
        “Beginner’s Guide to [Topic]: Everything You Need to Know”
        “Quick Tips: [Topic] for [Specific Audience]”
        “Master [Skill or Tool] with These Simple Steps”
        Listicle And Compilation Videos
        “Top 10 [Product/Tools/Tips] You Must Try”
        “Best [Product/Tools] of [Year]: Our Favorites Reviewed”
        “Essential [Topic] Ti¡ps You Should Know”
        “Most Amazing [Category] Transformations Caught on Camera”
        “Our Favorite [Category] Hacks You’ve Never Seen Before”
        Educational And Informative Videos
        “The Science Behind [Phenomenon or Trend]”
        “Understanding [Complex Topic] in Simple Terms”
        “Facts You Didn’t Know About [Topic]”
        “What Every [Audience] Should Know About [Topic]”
        “Inside Look: [Behind-the-Scenes of Topic or Event]”
        Entertainment And Lifestyle Videos
        “Ultimate Guide to [Activity or Hobby]”
        “Day in the Life of [Personality or Role]”
        “Exploring [Location or Trend]: Our Adventure”
        “Fun Challenges: [Challenge Name] vs. [Challenge Name]”
        “Our Favorite [Category] Reactions and Reviews”
        News And Trending Topics
        “Breaking News: [Headline or Event] Explained”
        “Latest Trends in [Industry or Niche]: What You Need to Know”
        “Hot Topic Debate: [Topic] vs. [Opposing View]”
        “Exclusive Interview with [Influential Figure or Celebrity]”
        “Update: [Current Event] and Its Impact on [Industry or Audience]”
        Reviews And Unboxings
        “Unboxing the Latest [Product]: First Impressions and Review”
        “In-Depth Review of [Gadget/Tech Item]: Is It Worth the Hype?”
        “Testing the Top [Brand] Products: Which One Reigns Supreme?”
        “Honest Review of [Service/Subscription]: What You Need to Know”
        “Unboxing and Review: [Product] vs. [Competitor]”
        Vlogs And Personal Experiences
        “A Day in My Life: Behind the Scenes of [Event/Activity]”
        “Weekly Vlog: How I Balance Work and Life”
        “Travel Vlog: Exploring [Destination] with Me”
        “My Morning Routine: How I Start My Day Energized”
        “Weekend Vlog: [Activity/Adventure] and What I Learned”
        YouTube Shorts And Quick Content
        “Quick Tips: [Topic] in 60 Seconds”
        “Instant Recipe: How to Make [Dish] in 1 Minute”
        “Fast Facts: [Interesting Fact or Trivia]”
        “One-Minute Challenge: [Fun Activity or Skill]”
        “Quick Hacks: Improve Your [Skill/Task] Easily”
        A Good Video Title Comes With Practice
        There is no guarantee an effective YouTube video title will immediately increase your viewership. However, it will improve your chances of being noticed and attract more viewers over time.
        The great thing about creating YouTube video titles is that you can change them at any time. Don’t be afraid to experiment with multiple titles to see what works best.
    </guidelines>

    IMPORTANT: Use always the language of the transcription

    YouTuber videos transcription:
    <video_data>
    {videos_string}
    </video_data>

    Return the data on an json list, do this only, do not return anything more
    [
        "My killer video title 1",
        "My killer video title 2",
        ...
    ]
    """
    response = _client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 2:
        print("Usage: python killer_video_title_gen.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    with open(video_path, "r", encoding="utf-8") as file:
        video_transcription = file.read()

    persona_tester = PersonaTester(
        model=OPENAI_MODEL,
        client=_client,
        comparation_path="videos_to_compare.json",
    )
    titles = gen_video_titles(video_transcription, persona_tester.ideas_to_generate)
    titles = try_to_load_json(_client, OPENAI_MODEL, titles)
    print("\n=== INITIAL VIDEO TITLES ===")
    print(titles)

    titles_results = persona_tester.test_multiples_videos(
        titles,
        checks=25,
        use_extra_titles=True,
    )

    print(f"\n=== {persona_tester.ideas_to_generate} FINAL VIDEO TITLES ===")
    print(titles_results)

    with open("output.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(titles_results))
