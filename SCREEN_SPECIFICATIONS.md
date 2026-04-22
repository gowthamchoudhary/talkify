# VoiceSnap Screen Specifications

## Design System

### Colors
- **Background**: `#050d05` (very dark green-black)
- **Primary**: `#4ade80` (bright green)
- **Cards**: `rgba(255,255,255,0.04)` (subtle white overlay)
- **Text**: `#ffffff` (white)
- **Muted text**: `rgba(255,255,255,0.5)` (50% white)

### Typography
- **Font**: system-ui, -apple-system, sans-serif
- **Headings**: bold, tight letter-spacing
- **Body**: 16px, 1.6 line-height

### Components
- **Buttons**: minimum 44px height, 14px border radius
- **Cards**: 20px border radius
- **Green glow**: subtle glow on primary elements
- **Mobile first**: max-width 480px, centered
- **Smooth transitions**: on all interactions

---

## Screen 1: HOME SCREEN

### Layout
```
┌─────────────────────────────────────┐
│                                     │
│            VoiceSnap 🎙️            │
│     "Everything has a voice.        │
│           Hear it."                 │
│                                     │
│                                     │
│         ┌─────────────────┐         │
│         │   📸 Snap & Meet │         │
│         │                 │         │
│         └─────────────────┘         │
│                                     │
│              📁 Gallery             │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

### Elements
1. **App Title**: "VoiceSnap 🎙️"
   - Large, bold text
   - Centered at top
   - White color (#ffffff)

2. **Tagline**: "Everything has a voice. Hear it."
   - Smaller text below title
   - Muted color (rgba(255,255,255,0.5))
   - Centered

3. **Primary Button**: "📸 Snap & Meet"
   - Large button (minimum 60px height)
   - Bright green background (#4ade80)
   - White text
   - Green glow effect
   - Triggers camera

4. **Gallery Option**: "📁 Gallery"
   - Secondary button style
   - Outline button with green border
   - Below camera button
   - Opens file picker

### Interactions
- Camera button → opens device camera
- Gallery button → opens file picker
- Both accept JPEG, PNG, WebP

---

## Screen 2: LOADING SCREEN

### Layout
```
┌─────────────────────────────────────┐
│                                     │
│         [User's Photo]              │
│                                     │
│                                     │
│            ⭕ Spinner               │
│                                     │
│           Awakening...              │
│                                     │
│     Discovering what you found...   │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

### Elements
1. **Photo Display**
   - User's captured/uploaded photo
   - Rounded corners (20px)
   - Centered, responsive size

2. **Loading Spinner**
   - Animated circular spinner
   - Green color (#4ade80)
   - Below photo

3. **Primary Text**: "Awakening..."
   - Large, bold text
   - White color
   - Centered below spinner

4. **Status Text** (cycles through):
   - "Discovering what you found..."
   - "Crafting its personality..."
   - "Designing its voice..."
   - Muted color (rgba(255,255,255,0.5))
   - Smooth transitions between messages

### Animations
- Spinner rotates continuously
- Status text fades in/out every 2-3 seconds
- Subtle pulse effect on photo

---

## Screen 3: MEET YOUR OBJECT

### Layout
```
┌─────────────────────────────────────┐
│                                     │
│               🐱                    │
│             Whiskers                │
│            Tabby Cat                │
│                                     │
│    [Curious] [Playful] [Wise]      │
│                                     │
│  A mysterious tabby cat who has     │
│  lived in the old library for       │
│  years, watching over ancient...    │
│                                     │
│  Voice: [Mysterious ▼]             │
│                                     │
│         ┌─────────┐ ┌─────────┐     │
│         │  TALK   │ │  SING   │     │
│         └─────────┘ └─────────┘     │
│                                     │
└─────────────────────────────────────┘
```

### Elements
1. **Object Emoji**
   - Large emoji (64px+)
   - Centered at top
   - Represents the object type

2. **Character Name**
   - Generated name (e.g., "Whiskers")
   - Large, bold text
   - White color
   - Centered below emoji

3. **Species/Type**
   - Object species (e.g., "Tabby Cat")
   - Smaller text
   - Muted color
   - Centered below name

4. **Personality Traits** (exactly 3)
   - Pill-shaped badges
   - Green background (#4ade80)
   - White text
   - Arranged horizontally
   - Examples: [Curious] [Playful] [Wise]

5. **Backstory**
   - Paragraph of generated backstory
   - Regular text size
   - White color
   - Left-aligned
   - Card background (rgba(255,255,255,0.04))

6. **Voice Selector**
   - Dropdown with 6 options:
     - Mysterious
     - Warm
     - Wise
     - Playful
     - Dramatic
     - Whispery
   - Green accent color

7. **Action Buttons**
   - **TALK**: Primary green button
   - **SING**: Secondary outline button
   - Side by side
   - Same height (44px minimum)

### Interactions
- Voice dropdown → changes voice style
- TALK button → goes to conversation screen
- SING button → goes to singing screen

---

## Screen 4: VOICE CONVERSATION

### Layout
```
┌─────────────────────────────────────┐
│              🐱 Whiskers            │
│             ● Speaking...           │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ User: Hello there!              │ │
│  │                                 │ │
│  │ Whiskers: Hello! I'm so excited │ │
│  │ to meet you! I've been waiting  │ │
│  │ in this library for someone...  │ │
│  │                                 │ │
│  │ User: Tell me about yourself    │ │
│  │                                 │ │
│  │ Whiskers: Well, I'm a curious   │ │
│  │ cat who loves books and...      │ │
│  └─────────────────────────────────┘ │
│                                     │
│              🎤 Hold to Speak       │
│                                     │
│              End Conversation       │
│                                     │
└─────────────────────────────────────┘
```

### Elements
1. **Character Header**
   - Emoji + name at top
   - Speaking status indicator
   - Pulse animation when speaking

2. **Conversation Transcript**
   - Scrollable chat area
   - Card background (rgba(255,255,255,0.04))
   - User messages: right-aligned, different color
   - AI messages: left-aligned, white text
   - Timestamps optional

3. **Microphone Button**
   - Large circular button
   - "🎤 Hold to Speak" text
   - Green when active
   - Records while held down

4. **End Button**
   - Secondary button
   - "End Conversation" text
   - Returns to previous screen

5. **Ambient Sound Indicator** (optional)
   - Small sound wave animation
   - Shows ambient audio is playing

### Interactions
- Hold mic button → records audio
- Release → sends to AI, gets response
- Auto-scroll transcript to bottom
- Ambient sounds play in background

---

## Screen 5: SINGING

### Layout
```
┌─────────────────────────────────────┐
│                                     │
│            🐱 ♪ ♫ ♪                │
│             Whiskers                │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ ♪ I'm Whiskers, curious and     │ │
│  │   free                          │ │
│  │   Adventure is what defines me  │ │
│  │   Through every day and every   │ │
│  │   night                         │ │
│  │   I shine my own unique light   │ │
│  │                                 │ │
│  │   That's my story, can't you    │ │
│  │   see?                          │ │
│  │   I'm Whiskers, just being me! ♪│ │
│  └─────────────────────────────────┘ │
│                                     │
│     ⏮️  ⏯️  ⏭️     2:34 / 3:12     │
│                                     │
│         Request Another Song        │
│                                     │
└─────────────────────────────────────┘
```

### Elements
1. **Character with Music Notes**
   - Emoji with floating music notes (♪ ♫ ♪)
   - Animated music notes
   - Character name below

2. **Lyrics Display**
   - Scrollable lyrics area
   - Card background
   - Current line highlighted
   - Synchronized with audio playback
   - Musical note (♪) at start/end

3. **Audio Player Controls**
   - Previous, Play/Pause, Next buttons
   - Progress bar with time display
   - Current time / Total duration
   - Green accent colors

4. **Request Button**
   - "Request Another Song" button
   - Secondary style
   - Generates new song with same character

### Interactions
- Play/pause controls audio
- Lyrics auto-scroll and highlight current line
- Progress bar shows playback position
- Request button → generates new song

---

## Mobile Responsive Guidelines

### Screen Sizes
- **Mobile**: 320px - 480px (primary target)
- **Tablet**: 481px - 768px
- **Desktop**: 769px+ (centered, max-width 480px)

### Touch Targets
- Minimum 44px height for all interactive elements
- Adequate spacing between touch targets (8px minimum)
- Swipe gestures for navigation (optional)

### Performance
- Smooth 60fps animations
- Fast loading transitions
- Optimized images and audio
- Progressive loading for large files

---

## Accessibility

### Requirements
- High contrast ratios (white on dark green)
- Screen reader support
- Keyboard navigation
- Focus indicators
- Alt text for images
- ARIA labels for interactive elements

### Audio
- Visual indicators for audio playback
- Captions/transcripts for generated speech
- Volume controls
- Audio descriptions where needed

---

## Technical Notes

### Image Handling
- Support JPEG, PNG, WebP
- Max file size: 10MB
- Auto-resize for display
- Maintain aspect ratio

### Audio Features
- WebRTC for microphone access
- WebSocket for real-time conversation
- Audio playback with controls
- Background ambient sounds

### State Management
- Persist conversation history
- Save voice preferences
- Handle network interruptions
- Graceful error recovery

---

## Animation Details

### Transitions
- Screen transitions: 300ms ease-in-out
- Button hover: 150ms ease
- Loading states: smooth fade in/out
- Pulse animations for speaking indicator

### Loading States
- Skeleton screens while loading
- Progressive image loading
- Spinner animations
- Status message transitions

This specification provides everything needed to design and implement the VoiceSnap mobile interface! 🎨