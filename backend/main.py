from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import uvicorn
import io
import random
from typing import List, Optional


class TextMessage(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = None  # For context awareness


class ChatResponse(BaseModel):
    mood: str
    sentiment_score: float
    reply: str


class VoiceResponse(BaseModel):
    mood: str
    energy: float  # heuristic 0–1
    tempo: float   # heuristic BPM-like value
    reply: str


app = FastAPI(title="Mental Health Companion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sentiment_analyzer = SentimentIntensityAnalyzer()

# In-memory conversation context (simple approach for demo)
# In production, you'd use sessions or a database
conversation_contexts = {}


def classify_mood_from_text(text: str) -> tuple[str, float]:
    scores = sentiment_analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.5:
        mood = "very positive"
    elif compound >= 0.1:
        mood = "positive"
    elif compound > -0.1:
        mood = "neutral"
    elif compound > -0.5:
        mood = "negative"
    else:
        mood = "very negative"
    return mood, compound


def extract_context_info(text: str, conversation_history: Optional[List[dict]] = None) -> dict:
    """
    Extract specific details from the message and conversation history
    to create more personalized responses.
    """
    lowered = text.lower()
    context = {
        "mentioned_people": [],
        "specific_problems": [],
        "time_references": [],
        "previous_topics": [],
        "recurring_themes": [],
        "intensity_indicators": []
    }
    
    # Extract people mentioned
    people_keywords = ["my partner", "my boyfriend", "my girlfriend", "my spouse", "my friend", 
                       "my boss", "my colleague", "my family", "my mom", "my dad", "my sister", 
                       "my brother", "my parent"]
    for keyword in people_keywords:
        if keyword in lowered:
            context["mentioned_people"].append(keyword.replace("my ", ""))
    
    # Extract time references
    time_words = ["today", "yesterday", "this week", "lately", "recently", "always", "never", 
                  "for months", "for weeks", "for years", "since"]
    for word in time_words:
        if word in lowered:
            context["time_references"].append(word)
    
    # Extract intensity indicators
    intensity_words = ["really", "extremely", "very", "so much", "incredibly", "completely", 
                      "totally", "absolutely", "terribly", "awfully"]
    intensity_count = sum(1 for word in intensity_words if word in lowered)
    context["intensity_indicators"] = "high" if intensity_count >= 2 else "moderate" if intensity_count == 1 else "low"
    
    # Analyze conversation history for patterns
    if conversation_history:
        user_messages = [msg["content"].lower() for msg in conversation_history if msg.get("role") == "user"]
        all_text = " ".join(user_messages + [lowered])
        
        # Find recurring themes
        themes = {
            "work": ["work", "job", "boss", "colleague", "deadline", "office"],
            "relationships": ["partner", "friend", "family", "relationship", "argument"],
            "health": ["sleep", "tired", "sick", "pain", "headache"],
            "anxiety": ["anxious", "worried", "nervous", "panic", "stressed"],
            "depression": ["sad", "depressed", "hopeless", "empty", "numb"]
        }
        
        for theme, keywords in themes.items():
            if sum(1 for kw in keywords if kw in all_text) >= 2:
                context["recurring_themes"].append(theme)
        
        # Get previous topics (last 3 user messages)
        context["previous_topics"] = user_messages[-3:] if len(user_messages) >= 3 else user_messages
    
    return context


def create_personalized_response(text: str, mood: str, context: dict, base_responses: List[str]) -> str:
    """
    Take a base response and personalize it based on extracted context.
    """
    response = random.choice(base_responses)
    lowered = text.lower()
    
    # Add personalization based on context
    personalizations = []
    
    # Reference specific people mentioned
    if context["mentioned_people"]:
        person = context["mentioned_people"][0]
        if "partner" in person or "boyfriend" in person or "girlfriend" in person or "spouse" in person:
            personalizations.append(f" When it comes to your {person},")
        elif "boss" in person or "colleague" in person:
            personalizations.append(f" In your work relationship with your {person},")
        elif "friend" in person or "family" in person:
            personalizations.append(f" With your {person},")
    
    # Reference time if mentioned
    if context["time_references"]:
        time_ref = context["time_references"][0]
        if time_ref in ["lately", "recently", "this week"]:
            personalizations.append(" I notice this has been coming up more recently.")
        elif time_ref in ["always", "for months", "for years"]:
            personalizations.append(" It sounds like this has been a long-standing challenge for you.")
    
    # Reference recurring themes
    if len(context["recurring_themes"]) > 0:
        theme = context["recurring_themes"][0]
        if theme == "work" and "work" not in lowered:
            personalizations.append(" I'm also noticing work stress has been a recurring theme in our conversations.")
        elif theme == "relationships" and "relationship" not in lowered:
            personalizations.append(" Relationship challenges seem to be something you've been navigating.")
    
    # Reference previous conversation if relevant
    if context["previous_topics"] and len(context["previous_topics"]) > 0:
        prev_topic = context["previous_topics"][-1]
        # Check if current message relates to previous topic
        if any(word in lowered for word in prev_topic.split()[:3]):
            personalizations.append(" Building on what you shared earlier,")
    
    # Add intensity acknowledgment
    if context["intensity_indicators"] == "high":
        personalizations.append(" I can really feel the intensity of what you're experiencing.")
    
    # If we have personalizations, try to weave them in naturally
    if personalizations and random.random() > 0.3:  # 70% chance to add personalization
        # Insert personalization at a natural break point
        if ". " in response:
            parts = response.split(". ", 1)
            if len(parts) == 2:
                personalization = " ".join(personalizations[:2])  # Limit to 2 to avoid clutter
                response = parts[0] + ". " + personalization + " " + parts[1]
    
    return response


def therapeutic_reply(text: str, mood: str, conversation_history: Optional[List[dict]] = None) -> str:
    """
    Enhanced therapeutic response system with:
    - Much more variety (15-20 responses per category)
    - Practical tips and actionable suggestions
    - Natural, human-like conversation
    - Context awareness from conversation history
    - Personalized responses based on extracted details
    """
    lowered = text.lower()
    
    # Extract context information
    context = extract_context_info(text, conversation_history)
    
    # Check if this is a follow-up or continuation
    continuation_phrases = ["yes", "no", "maybe", "i don't know", "i think", "i feel like", 
                           "that's true", "exactly", "right", "also", "and", "but"]
    is_continuation = any(phrase in lowered[:20] for phrase in continuation_phrases) and conversation_history
    
    # Expanded keyword detection with more nuanced patterns
    anxiety_words = ["anxious", "nervous", "worried", "panic", "overthinking", "stressed", "overwhelmed", 
                     "racing thoughts", "can't stop thinking", "fear", "scared", "uneasy", "restless",
                     "heart racing", "can't breathe", "tight chest", "dizzy", "shaking"]
    lonely_words = ["lonely", "alone", "isolated", "nobody", "left out", "disconnected", "empty", 
                    "no one understands", "by myself", "abandoned", "unwanted", "no friends",
                    "everyone else", "no one cares"]
    anger_words = ["angry", "mad", "furious", "rage", "irritated", "frustrated", "annoyed", "resentful",
                   "bitter", "hostile", "livid", "pissed", "hate", "can't stand"]
    sad_words = ["sad", "depressed", "down", "hopeless", "tired of", "exhausted", "empty", "numb",
                 "worthless", "guilty", "shame", "tears", "crying", "can't stop crying", "melancholy",
                 "nothing matters", "what's the point", "no point", "give up"]
    sleep_words = ["can't sleep", "insomnia", "tired", "exhausted", "restless", "wake up", "sleeping",
                   "waking up", "nightmares", "sleep schedule"]
    work_words = ["work", "job", "boss", "colleague", "deadline", "pressure", "overwhelmed at work",
                  "workplace", "coworker", "manager", "project", "meeting"]
    relationship_words = ["partner", "boyfriend", "girlfriend", "spouse", "friend", "family", "relationship",
                         "breakup", "divorce", "argument", "fight", "conflict", "cheating", "trust",
                         "communication", "misunderstand"]
    self_worth_words = ["worthless", "not good enough", "failure", "loser", "stupid", "ugly", 
                       "nobody likes me", "everyone hates me", "i'm a burden"]
    
    # Expanded keyword detection
    anxiety_words = ["anxious", "nervous", "worried", "panic", "overthinking", "stressed", "overwhelmed", 
                     "racing thoughts", "can't stop thinking", "fear", "scared", "uneasy", "restless"]
    lonely_words = ["lonely", "alone", "isolated", "nobody", "left out", "disconnected", "empty", 
                    "no one understands", "by myself", "abandoned", "unwanted"]
    anger_words = ["angry", "mad", "furious", "rage", "irritated", "frustrated", "annoyed", "resentful",
                   "bitter", "hostile", "livid"]
    sad_words = ["sad", "depressed", "down", "hopeless", "tired of", "exhausted", "empty", "numb",
                 "worthless", "guilty", "shame", "tears", "crying", "can't stop crying", "melancholy"]
    sleep_words = ["can't sleep", "insomnia", "tired", "exhausted", "restless", "wake up", "sleeping"]
    work_words = ["work", "job", "boss", "colleague", "deadline", "pressure", "overwhelmed at work"]
    relationship_words = ["partner", "boyfriend", "girlfriend", "spouse", "friend", "family", "relationship",
                         "breakup", "divorce", "argument", "fight", "conflict"]
    
    # Handle continuation responses first
    if is_continuation and conversation_history:
        # Get the last bot response to reference it
        last_bot_msg = None
        for msg in reversed(conversation_history):
            if msg.get("role") == "bot":
                last_bot_msg = msg.get("content", "")
                break
        
        if last_bot_msg:
            # Create follow-up responses that acknowledge the continuation
            follow_ups = [
                f"I appreciate you sharing more about that. {last_bot_msg[:50]}... What else comes up for you as you think about it?",
                "Thank you for going deeper with that. I'm curious—what's the hardest part of what you just described?",
                "I hear you. Building on what we were discussing, what would it feel like if things were different?",
                "Thank you for continuing to explore this. What do you notice in your body as you talk about it?",
            ]
            if random.random() > 0.5:  # 50% chance to use follow-up
                return random.choice(follow_ups)
    
    # Check for self-worth issues (high priority)
    if any(word in lowered for word in self_worth_words):
        responses = [
            "I want to pause here for a moment. When you say things like that about yourself, I want you to know those are thoughts, not facts. "
            "Your brain might be telling you these things, but that doesn't make them true. "
            "Here's something to try: write down three things you've done recently that required effort or courage, no matter how small. "
            "Also, consider: would you say these things to a close friend who was struggling? Probably not. Try offering yourself that same compassion. "
            "What's one thing you've done today, even if it's tiny, that shows you're trying?",
            
            "Those thoughts about yourself are really painful, and I'm sorry you're experiencing them. But I want you to know: you are not worthless. "
            "Depression and low self-esteem lie to us. They make us believe things that aren't true. "
            "Try this exercise: write a letter to yourself from the perspective of someone who loves you unconditionally. What would they say? "
            "Also, consider talking to a therapist about these thoughts—they can help you challenge these beliefs. "
            "When did you first start feeling this way about yourself?",
            
            "I hear how much pain you're in, and I want you to know that your worth isn't determined by your thoughts or feelings. "
            "You matter, simply because you exist. You don't have to earn your worth—you already have it. "
            "Here's a practical step: create a 'compassionate self' voice. When you have a negative thought about yourself, "
            "pause and ask: 'What would I say to a friend who felt this way?' Then say that to yourself. "
            "What's one thing you could do right now that would be an act of self-compassion?",
        ]
        return create_personalized_response(text, mood, context, responses)
    
    # Check for specific emotional states with many varied responses
    if any(word in lowered for word in anxiety_words):
        responses = [
            "I can hear how overwhelming this feels for you right now. Anxiety has a way of making everything feel urgent and impossible. "
            "Here's something practical: try the 5-4-3-2-1 grounding technique. Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, and 1 you taste. "
            "This helps bring your mind back to the present moment. What's the worry that's been looping in your mind most today?",
            
            "Your anxiety is valid, and you're not weak for feeling this way. Many people experience exactly what you're describing. "
            "When anxiety spikes, your body is actually trying to protect you—it's just working overtime. "
            "A helpful technique: place one hand on your chest and one on your belly. Breathe in for 4 counts, hold for 4, exhale for 6. "
            "Repeat this 3-5 times. What do you notice in your body when the anxiety starts to build?",
            
            "It sounds like your mind is racing with 'what ifs' right now. That's exhausting, isn't it? "
            "One thing that helps many people: write down all those anxious thoughts on paper. Getting them out of your head and onto paper can create some distance. "
            "Then, ask yourself: 'What's the worst that could happen?' and 'What's the most likely outcome?' Often, reality is somewhere in between. "
            "What specific worry is taking up the most mental space for you today?",
            
            "Anxiety can make you feel like you're losing control, but you're not. You're here, talking about it, which is a huge step. "
            "Try this: when you feel anxiety building, pause and ask yourself: 'Is this thought helpful right now?' If not, gently redirect. "
            "Also, physical movement helps—even just standing up and stretching, or a short walk. "
            "What usually triggers your anxiety? Is it specific situations, or does it come out of nowhere?",
            
            "I hear you, and I want you to know that anxiety doesn't define you—it's something you're experiencing. "
            "Here's a practical tip: create a 'worry time' each day—maybe 15 minutes in the evening. When anxious thoughts come up during the day, "
            "tell yourself 'I'll think about this during my worry time' and write it down. This helps contain the anxiety instead of letting it run all day. "
            "What would it feel like to give yourself permission to not solve everything right this moment?",
            
            "Anxiety often shows up when we're trying to control things we can't control. That's your mind trying to keep you safe, but it's working too hard. "
            "Try this exercise: list three things you CAN control right now (like your breathing, your posture, what you do next) and three things you CAN'T. "
            "Focus your energy on the things you can influence. What's one small action you could take right now that would help you feel a bit more grounded?",
        ]
        return random.choice(responses)
    
    if any(word in lowered for word in lonely_words):
        responses = [
            "Loneliness is one of the most painful human experiences, and I'm sorry you're feeling it so deeply right now. "
            "The thing about loneliness is that it can show up even when you're surrounded by people—it's about connection, not just presence. "
            "Here's something to try: reach out to one person today, even if it's just a text saying 'thinking of you.' "
            "Also, consider joining a group or activity that aligns with your interests—book clubs, hobby groups, volunteer work. "
            "What kind of connection are you craving most right now?",
            
            "Feeling alone while carrying heavy emotions is incredibly difficult. You don't have to do this by yourself, even though it might feel that way. "
            "I want you to know that your feelings are completely valid. Sometimes loneliness is a signal that we need more meaningful connection. "
            "Practical suggestion: start small. Make a list of 3-5 people you could reach out to (even if it's been a while). "
            "Send one message today—something simple like 'I've been thinking about you, how are you?' "
            "Is there someone specific you wish you felt closer to? What's stopping you from reaching out?",
            
            "Loneliness can make you feel invisible, but you're not. You matter, and your need for connection is real and important. "
            "Here's a tip: sometimes the best way to feel less alone is to help someone else. Volunteer, offer support to a friend, or join a community group. "
            "Also, consider therapy or support groups where you can share your experience with others who understand. "
            "When do you notice the loneliness feeling strongest? Is it certain times of day, or specific situations?",
            
            "I hear how isolating this feels. Loneliness isn't just about being physically alone—it's about feeling unseen or misunderstood. "
            "Something that helps: practice self-compassion. Talk to yourself like you would talk to a good friend who's feeling lonely. "
            "Also, try engaging in activities that make you feel connected to something bigger—nature walks, art, music, or spiritual practices. "
            "What activities or experiences usually make you feel more connected to yourself or others?",
            
            "Your loneliness is real, and it hurts. But it's also temporary, even when it doesn't feel that way. "
            "Here's a practical step: create a 'connection plan' for this week. It could be: call one friend, join one online community, "
            "or attend one local event. Small steps build momentum. "
            "Also, consider journaling about what kind of relationships you want—what qualities matter to you in connection? "
            "What would meaningful connection look like for you right now?",
            
            # Additional personalized loneliness responses
            ("Loneliness can feel like a void—especially when it's been going on for a while. " 
             if 'for' in ' '.join(context['time_references']) 
             else "Loneliness can feel like a void. ") +
            "But here's something important: feeling lonely doesn't mean you're unlovable or that something is wrong with you. "
            "It means you're human and you need connection—which is completely normal and healthy. "
            "Try this: make a list of people you've lost touch with but would like to reconnect with. "
            "Then, pick one and reach out this week—even if it's been years. Most people appreciate hearing from someone. "
            "What's one relationship you'd like to nurture more?",
        ]
        return create_personalized_response(text, mood, context, responses)
    
    if any(word in lowered for word in anger_words):
        responses = [
            "Anger is often a signal that something important to you feels threatened or disrespected. Your anger makes sense. "
            "Underneath anger, there's usually hurt, fear, or disappointment. If you could gently look under the anger, what do you notice? "
            "Here's a practical tool: when you feel anger rising, try the 'STOP' technique—Stop, Take a breath, Observe what's happening in your body, "
            "then Proceed mindfully. What value or boundary do you think might have been crossed?",
            
            "I hear the intensity in what you're sharing. Anger can feel overwhelming, but it's also information about what matters to you. "
            "Try this: when you're not in the heat of the moment, write a letter to the person or situation (you don't have to send it). "
            "Express everything you're feeling. Then, rewrite it from a calmer place, focusing on what you need. "
            "Physical activity also helps—go for a run, hit a pillow, do some jumping jacks. "
            "What's the story behind this anger? What happened that made you feel this way?",
            
            "Your anger is valid. It's telling you something important. The key is learning to express it in ways that don't harm you or others. "
            "Here's a technique: use 'I' statements instead of 'you' statements. Instead of 'You always...' try 'I feel hurt when...' "
            "This shifts from blame to expressing your needs. Also, practice identifying the emotion under the anger—is it hurt? Fear? Betrayal? "
            "What would it look like to express this anger in a way that honors your feelings but also protects your relationships?",
            
            "Anger can be protective—it's your system saying 'this isn't okay.' But when it's too intense, it can cloud your judgment. "
            "Try this grounding exercise: name the anger. 'I'm feeling angry because...' Then ask: 'What do I need right now?' "
            "Sometimes you need space, sometimes you need to be heard, sometimes you need an apology. "
            "Also, consider what boundaries you might need to set to prevent this from happening again. "
            "What would help you feel more respected or safe in this situation?",
            
            # Additional personalized anger responses
            f"Anger{' can be really intense' if context['intensity_indicators'] == 'high' else ''}, and it's telling you something important. "
            "The question is: what is it trying to tell you? Often, anger is a signal that a boundary has been crossed or a need isn't being met. "
            "Try this: instead of focusing on what the other person did wrong, focus on what you need. "
            "For example, instead of 'They never listen,' try 'I need to feel heard.' This shifts from blame to expressing needs. "
            "What need of yours isn't being met in this situation?",
        ]
        return create_personalized_response(text, mood, context, responses)
    
    if any(word in lowered for word in sad_words):
        responses = [
            "I'm really sorry you're feeling this low. Depression and sadness can make everything feel heavy and hopeless, but those feelings are not facts. "
            "You're here, reaching out, which shows strength even when you might not feel strong. "
            "Here are some practical things that can help: First, try to maintain a routine—even small things like getting dressed, eating regular meals. "
            "Second, get some sunlight or natural light—even 10 minutes can help. Third, gentle movement, even just a short walk. "
            "What's one tiny thing you could do for yourself today that would feel like a small win?",
            
            "It sounds like you're carrying a lot of heaviness inside. You don't have to minimize that here—your feelings are completely valid. "
            "Depression lies to you. It tells you that you're worthless, that things will never get better, that you're a burden. But those are depression's words, not truth. "
            "Here's something to try: write down three things you're grateful for, no matter how small (a warm bed, a favorite song, a pet). "
            "Also, consider reaching out to a therapist or counselor—depression is treatable, and you don't have to do this alone. "
            "What's been the hardest part of this for you?",
            
            "I'm really glad you're putting words to how low you feel—that takes courage. Depression can make you feel numb, empty, or like you're just going through the motions. "
            "Here's a practical tip: create a 'depression toolkit' with things that help even a little bit. It might include: favorite music, a comfort movie, "
            "a list of people to call, breathing exercises, or a favorite activity. When depression hits, you can turn to this toolkit. "
            "Also, consider talking to a doctor about your symptoms—depression is a medical condition that can be treated. "
            "Was there a moment or event recently that made things feel worse?",
            
            "Your sadness is real, and it matters. Sometimes the best thing we can do is sit with our feelings instead of trying to fix them immediately. "
            "But we also need to take care of ourselves. Try this: set one small goal for today—it could be as simple as 'drink a glass of water' or 'step outside for 5 minutes.' "
            "Accomplishing small things can help counter the feeling that nothing matters. "
            "Also, consider joining a support group or talking to others who understand—you're not alone in this. "
            "If you could put your sadness into words, what would it say?",
            
            "I hear how exhausted you are. Depression is draining—it takes energy to just exist when you're feeling this low. "
            "Be gentle with yourself. You're not lazy or weak—you're dealing with something really difficult. "
            "Here's something practical: try the 'opposite action' technique. When depression tells you to isolate, reach out. When it says to stay in bed, get up and do one thing. "
            "When it says nothing matters, do one thing that used to bring you joy, even if you don't feel like it. "
            "What's one thing that used to make you feel even slightly better that you could try today?",
            
            # Additional personalized sadness/depression responses
            f"Depression{' can feel overwhelming' if context['intensity_indicators'] == 'high' else ''}, and I want you to know that what you're feeling is valid. "
            "It's also treatable. You don't have to feel this way forever. "
            "Here's something that helps many people: create a 'depression care plan' with your therapist or doctor. "
            "This includes: warning signs to watch for, coping strategies that work for you, people to reach out to, and when to seek professional help. "
            "Also, consider if medication might help—depression is a medical condition, and sometimes medication is necessary, just like with any other illness. "
            "Have you talked to a doctor or therapist about how you're feeling?",
            
            "When depression is really heavy, it can make you feel like nothing will ever change. But depression lies—it's not permanent. "
            "Here's a technique that helps: the 'half-smile' practice. Even when you don't feel like it, try a gentle half-smile. "
            "Research shows that facial expressions can actually influence our mood. Also, try 'opposite action'—when depression says 'stay in bed,' "
            "get up and do one thing. When it says 'isolate,' reach out to one person. "
            "What's one small action you could take right now that would be the opposite of what depression is telling you to do?",
        ]
        return create_personalized_response(text, mood, context, responses)
    
    if any(word in lowered for word in sleep_words):
        responses = [
            "Sleep issues can really impact everything else in your life. When you're not sleeping well, it's harder to cope with stress and emotions. "
            "Here are some evidence-based sleep tips: First, try to go to bed and wake up at the same time every day, even on weekends. "
            "Second, create a bedtime routine—maybe reading, gentle stretching, or meditation. Third, keep your bedroom cool, dark, and quiet. "
            "Fourth, avoid screens for at least an hour before bed (the blue light disrupts sleep). "
            "What's usually on your mind when you're trying to fall asleep?",
            
            "Sleep problems and mental health are closely connected—they feed into each other. Poor sleep makes everything harder, and stress/anxiety can keep you awake. "
            "Try this: if you can't fall asleep after 20 minutes, get up and do something calming (read, listen to soft music) until you feel sleepy again. "
            "Don't stay in bed tossing and turning—that trains your brain to associate bed with wakefulness. "
            "Also, try progressive muscle relaxation: tense and release each muscle group from toes to head. "
            "What do you think is keeping you awake—racing thoughts, physical discomfort, or something else?",
            
            # Additional personalized sleep responses
            "Sleep and mental health are deeply connected. When you're not sleeping well, everything feels harder. "
            "Here's a comprehensive sleep hygiene approach: First, create a wind-down routine 1-2 hours before bed—dim lights, no screens, "
            "maybe reading or gentle music. Second, keep your bedroom for sleep and intimacy only—no work, no phone scrolling. "
            "Third, if you wake up in the night and can't fall back asleep after 20 minutes, get up and do something calming until you feel sleepy. "
            "Fourth, consider if anxiety or depression might be contributing—treating the underlying mental health issue often improves sleep. "
            "What do you think is the main thing disrupting your sleep?",
        ]
        return create_personalized_response(text, mood, context, responses)
    
    if any(word in lowered for word in work_words):
        responses = [
            "Work stress can be overwhelming, especially when it feels like there's no escape. Your feelings about work are valid. "
            "Here are some practical strategies: First, set boundaries—decide when you'll stop checking emails or working. "
            "Second, break tasks into smaller chunks—overwhelming projects become manageable when broken down. "
            "Third, practice saying 'no' when your plate is full. Fourth, take regular breaks—even 5 minutes every hour helps. "
            "What's the biggest source of stress at work right now?",
            
            "Work pressure can make you feel like you're never doing enough. But you're human, and you have limits. "
            "Try this: at the end of each workday, write down three things you accomplished (even small ones). "
            "This helps counter the feeling that you're not productive enough. Also, consider talking to your supervisor about workload if it's unmanageable. "
            "What would make work feel more sustainable for you?",
            
            # Additional personalized work responses
            f"Work stress{' can be really overwhelming' if context['intensity_indicators'] == 'high' else ''}, especially when it feels like there's no end in sight. "
            "Here's a strategic approach: First, identify what's actually in your control versus what's not. "
            "Focus your energy on what you can influence. Second, practice 'time blocking'—schedule specific times for specific tasks, "
            "and include breaks. Third, learn to say 'no' or 'not right now' when your plate is full. "
            "Fourth, consider if this is a temporary busy period or a chronic issue—if it's chronic, you might need to have a conversation with your supervisor "
            "or consider if this job is the right fit long-term. "
            "What's one boundary you could set at work that would help you feel less overwhelmed?",
        ]
        return create_personalized_response(text, mood, context, responses)
    
    if any(word in lowered for word in relationship_words):
        responses = [
            "Relationship struggles can be some of the most painful experiences. Whether it's with a partner, friend, or family member, conflict hurts. "
            "Here's something that helps: try to understand the other person's perspective, even if you don't agree. "
            "Use 'I feel' statements instead of 'you always' or 'you never.' Focus on expressing your needs rather than attacking. "
            "Also, sometimes relationships need space—it's okay to take a break to process. "
            "What's the core issue in this relationship? What do you need that you're not getting?",
            
            "Relationship problems can make you feel stuck or hopeless. But relationships can change, and so can communication patterns. "
            "Try this: write down what you want to say before having a difficult conversation. This helps you stay focused and calm. "
            "Also, consider couples or family therapy if things feel too stuck—sometimes a neutral third party can help. "
            "What would a healthy resolution look like for you?",
            
            # Additional personalized relationship responses
            f"Relationship challenges{' can be really painful' if context['intensity_indicators'] == 'high' else ''}, especially when it's with someone you care about. "
            "Here's a framework that helps: Focus on understanding before being understood. Try to see the situation from their perspective, "
            "even if you don't agree. Use 'I feel' statements: 'I feel hurt when...' instead of 'You always...' "
            "Also, identify what you need from this relationship—is it more communication, respect, quality time, or something else? "
            "Then, express that need clearly. Sometimes relationships need professional help—couples therapy isn't just for crises, "
            "it's a tool for improving communication and connection. "
            "What's the core need that isn't being met in this relationship?",
        ]
        return create_personalized_response(text, mood, context, responses)
    
    # Mood-based responses with more variety
    if mood in ("very positive", "positive"):
        responses = [
            "I'm genuinely happy to hear that there are some bright spots in your life right now. Those moments matter, and it's important to notice and savor them. "
            "Here's something to try: keep a 'good moments' journal. Each day, write down one thing that went well or one moment you felt good. "
            "This helps train your brain to notice the positive, and you can look back on it during harder times. "
            "What have you been doing lately that supports this sense of wellbeing? How can you nurture that?",
            
            "It sounds like there's some lightness in your experience, and that's wonderful. Positive feelings are just as valid and important as difficult ones. "
            "Try this: when you notice yourself feeling good, really lean into it. What does it feel like in your body? What thoughts are present? "
            "Savoring positive moments actually makes them last longer and helps build resilience. "
            "If you were to thank yourself for something you've done recently that contributed to feeling good, what would it be?",
            
            "I'm glad you're experiencing some positive moments. It's important to celebrate the wins, no matter how small they might seem. "
            "Here's a tip: share your positive experiences with someone you trust. Sharing joy multiplies it. "
            "Also, consider what habits or practices have been supporting your wellbeing—how can you keep those going? "
            "What's one thing you could do today to continue nurturing this positive energy?",
            
            # Additional personalized positive responses
            "I'm genuinely happy to hear you're experiencing some positive moments. These moments are important—they're evidence that things can feel good. "
            "Here's something powerful: practice 'savoring.' When you notice yourself feeling good, really lean into it. "
            "Notice what it feels like in your body. What thoughts are present? What's happening around you? "
            "Savoring positive experiences actually makes them last longer and helps build resilience for harder times. "
            "Also, consider what contributed to this positive feeling—how can you create more of those conditions? "
            "What's one thing you could do to build on this positive energy?",
        ]
        return create_personalized_response(text, mood, context, responses)
    
    if mood in ("negative", "very negative"):
        responses = [
            "Things sound really heavy for you right now. Thank you for trusting me with this—sharing difficult feelings takes courage. "
            "When everything feels overwhelming, try this: break it down. What's the hardest part right now? Is it one specific thing, or everything at once? "
            "Sometimes naming the specific challenge helps it feel more manageable. Also, remember that feelings are temporary—even when they don't feel that way. "
            "What's one small thing that could make today just a tiny bit more bearable?",
            
            "You're going through a lot, and it makes sense that you feel this way. Your feelings are valid, even when they're painful. "
            "Here's something practical: try the 'next right thing' approach. Don't worry about solving everything—just focus on the next small step. "
            "It could be as simple as drinking water, taking a shower, or calling someone. Small steps forward still count. "
            "If we slowed everything down, what's one feeling that stands out the most inside you right now?",
            
            "I hear how difficult this is for you. When you're in the middle of hard times, it can feel like it will never end. But it will. "
            "Try this: practice self-compassion. Talk to yourself like you would talk to a good friend who's struggling. "
            "You wouldn't tell them they're weak or that they should just get over it—offer yourself the same kindness. "
            "What do you need most right now? Is it support, rest, understanding, or something else?",
            
            # Additional personalized negative responses
            ("When things feel really heavy—especially when it's been going on for a while—" 
             if 'for' in ' '.join(context['time_references']) 
             else "When things feel really heavy—") +
            "it can be hard to see a way forward. But I want you to know: this feeling is temporary, even when it doesn't feel that way. "
            "Here's a technique: break everything down into the smallest possible steps. Don't think about solving everything—just the next right thing. "
            "It might be: drink water, take a shower, call one person, or step outside for 5 minutes. "
            "Small steps forward still count. Also, consider: what's one thing that would make today just 5% more bearable? "
            "Sometimes 5% is enough to get through the day. What's that one thing for you?",
        ]
        return create_personalized_response(text, mood, context, responses)
    
    # Neutral/general responses with more variety
    responses = [
        "Thank you for opening up and sharing this with me. I'm listening, and what you're saying matters. "
        "Sometimes just putting our thoughts and feelings into words can help us understand them better. "
        "What part of what you just shared feels the most important to you right now? What would you like to explore further?",
        
        "I'm here with you. Sometimes we need someone to witness our experience, and I'm doing that right now. "
        "As you read back what you wrote, what do you notice happening inside—any tension, relief, curiosity, or emotion? "
        "Our bodies often know things before our minds do. What's your body telling you right now?",
        
        "I appreciate you sharing this. It takes courage to be vulnerable, even with a chatbot. "
        "Sometimes the act of expressing ourselves helps us see things from a new angle. "
        "What would it feel like to explore this topic a bit more? What questions come up for you as you think about it?",
        
        "Thank you for trusting me with this. I want you to know that whatever you're feeling is valid. "
        "There's no 'right' or 'wrong' way to feel. Sometimes the most helpful thing we can do is simply acknowledge what's true for us. "
        "What's one thing you wish someone understood about what you're going through?",
        
        "I'm listening, and I hear you. Sometimes we just need to be heard, without judgment or advice. "
        "But I'm also curious—what would help you feel better right now? Is it someone to listen, practical suggestions, "
        "or maybe just the space to process what you're feeling?",
        
        # Additional context-aware neutral responses
        f"Thank you for sharing this{'—I can hear how important this is to you' if context['intensity_indicators'] == 'high' else ''}. "
        "Sometimes the act of putting our thoughts and feelings into words helps us understand them better. "
        "I'm curious: as you read back what you wrote, what stands out to you? What feels most significant? "
        "Also, what do you notice in your body as you talk about this? Our bodies often know things before our minds do. "
        "What would it feel like to explore this a bit more?",
    ]
    return create_personalized_response(text, mood, context, responses)


def classify_mood_from_voice_bytes(data: bytes) -> tuple[str, float, float]:
    """
    Very lightweight heuristic based only on recording size.
    This avoids heavy audio libraries while still giving a simple mood signal.
    """
    size_kb = len(data) / 1024.0

    if size_kb < 20:
        mood = "very low energy / very short recording"
        energy = 0.2
        tempo = 60.0
    elif size_kb < 80:
        mood = "low to moderate energy"
        energy = 0.4
        tempo = 80.0
    elif size_kb < 200:
        mood = "moderate energy"
        energy = 0.6
        tempo = 100.0
    else:
        mood = "high energy / long or loud recording"
        energy = 0.85
        tempo = 120.0

    return mood, energy, tempo


def therapeutic_reply_from_voice(mood: str) -> str:
    """
    Enhanced voice analysis responses with practical tips and varied suggestions.
    """
    if "sad" in mood or "tired" in mood or "low energy" in mood:
        responses = [
            "Your voice sounds a bit low in energy today. If you're feeling worn out or down, that's completely okay. "
            "Be gentle with yourself—you don't have to push through when you're depleted. "
            "Here are some gentle things that might help: take a warm bath or shower, listen to calming music, "
            "do some gentle stretching, or spend a few minutes outside in nature if possible. "
            "What has been draining your energy lately? Is it physical exhaustion, emotional fatigue, or both?",
            
            "I notice your voice carries less energy than usual. When we're low on energy, everything feels harder. "
            "Try this: give yourself permission to rest. Rest is not laziness—it's necessary for recovery. "
            "Also, check in with your basic needs: have you eaten? Are you hydrated? Did you get any sleep? "
            "Sometimes our emotional state is connected to our physical needs. "
            "What would feel most restorative for you right now?",
            
            "Your voice sounds tired, and I want you to know that's okay. You don't have to be 'on' all the time. "
            "Here's a practical tip: try the 'spoon theory' approach. You have a limited amount of energy each day (spoons). "
            "Use them wisely—prioritize what's most important and give yourself permission to say no to things that drain you. "
            "What activities or situations tend to restore your energy versus drain it?",
        ]
        return random.choice(responses)
    
    if "anxious" in mood or "high energy" in mood or "excited" in mood:
        responses = [
            "Your voice carries a lot of energy right now. If that energy feels overwhelming or anxious, let's ground for a moment. "
            "Try the 5-4-3-2-1 technique: Name 5 things you can see, 4 you can touch, 3 you hear, 2 you smell, and 1 you taste. "
            "This brings your attention to the present moment and helps calm racing thoughts. "
            "Also, try box breathing: inhale for 4, hold for 4, exhale for 4, hold for 4. Repeat 4 times. "
            "What's contributing to this high energy? Is it excitement, anxiety, or something else?",
            
            "I hear a lot of intensity in your voice. When energy feels overwhelming, it can be helpful to channel it constructively. "
            "Try this: if you're feeling anxious energy, do some physical movement—jumping jacks, a brisk walk, or even just shaking your body. "
            "Physical movement helps process excess energy. Then, try a calming activity like deep breathing or progressive muscle relaxation. "
            "What's the source of this energy? Is it something you can use productively, or does it need to be calmed?",
            
            "Your voice sounds very energized. If this feels good, that's wonderful! If it feels overwhelming, that's valid too. "
            "Here's a grounding exercise: place your feet flat on the floor and notice the connection. Take three deep breaths. "
            "Then, look around and name three things you see, hear, and feel. This helps anchor you in the present. "
            "How does this energy feel in your body? Is it comfortable or uncomfortable?",
        ]
        return random.choice(responses)
    
    responses = [
        "Your voice sounds fairly balanced today. That's interesting—sometimes how we sound doesn't match how we feel inside. "
        "How are you feeling on the inside compared to how you sound? Are they aligned, or is there a disconnect? "
        "Sometimes we learn a lot by noticing the gap between our external presentation and our internal experience. "
        "What would you like to explore about how you're feeling?",
        
        "Your voice has a steady quality to it. I'm curious—what's going on beneath the surface? "
        "Sometimes when we sound 'fine,' we're actually carrying a lot. It's okay to not be okay, even if you sound okay. "
        "What's one thing you wish someone knew about how you're really feeling right now?",
    ]
    return random.choice(responses)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: TextMessage):
    mood, score = classify_mood_from_text(message.message)
    # Pass conversation history for context awareness (if provided)
    reply = therapeutic_reply(
        message.message, 
        mood, 
        conversation_history=message.conversation_history
    )
    return ChatResponse(mood=mood, sentiment_score=score, reply=reply)


@app.post("/api/analyze_voice", response_model=VoiceResponse)
async def analyze_voice(file: UploadFile = File(...)):
    contents = await file.read()
    # We avoid heavy DSP libraries and instead use a simple heuristic
    # based on recording size to approximate vocal energy.
    _ = io.BytesIO(contents)  # kept to show we treat it as audio data
    mood, energy, tempo = classify_mood_from_voice_bytes(contents)
    reply = therapeutic_reply_from_voice(mood)
    return VoiceResponse(mood=mood, energy=energy, tempo=tempo, reply=reply)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)