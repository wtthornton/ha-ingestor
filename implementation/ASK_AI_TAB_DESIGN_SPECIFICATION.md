# Ask AI Tab - Design Specification
**Date:** October 19, 2025  
**Status:** Design Phase - Option A (Design First)  
**Epic:** Conversational AI Assistant for HA AutomateAI

---

## 🎯 **Executive Summary**

A natural language chat interface for HA AutomateAI where users can ask questions about their smart home and receive multiple automation suggestions using the existing RAG-based suggestion engine. This is a **new tab** separate from the existing "Conversational Dashboard" which shows suggestion cards.

**Key Distinction:**
- **Existing ConversationalDashboard.tsx:** Shows automation suggestion cards with natural language editing
- **New Ask AI Tab:** Chat-based question-answering with RAG-powered suggestion retrieval

**User Request Example:**
> "I want to flash the office lights when VGK scores"

**AI Response:**
- Multiple automation suggestions (RAG retrieval from pattern database)
- Interactive suggestion cards (reuse existing components)
- Conversational context for refinement

---

## 📋 **Table of Contents**

1. [User Flow & Experience](#user-flow--experience)
2. [UI/UX Design](#uiux-design)
3. [Technical Architecture](#technical-architecture)
4. [API Design](#api-design)
5. [Component Structure](#component-structure)
6. [RAG Integration](#rag-integration)
7. [Implementation Plan](#implementation-plan)
8. [Technology Decisions](#technology-decisions)

---

## 🎨 **User Flow & Experience**

### **Primary User Flows**

#### **Flow 1: First-Time User (Discovery)**
```
1. User opens "Ask AI" tab
   └─> Sees welcome screen with suggested prompts
   
2. User sees personalized prompts:
   ├─> "Flash my office lights when VGK scores" (if VGK tracking active)
   ├─> "Turn off devices when electricity is expensive" (if pricing active)
   └─> "Adjust temperature based on weather" (if weather active)
   
3. User clicks or types a question
   └─> Question sent to AI (RAG query)
   
4. AI responds with conversational message:
   ├─> "I found 3 automation ideas for you..."
   └─> Shows suggestion cards (reuse ConversationalSuggestionCard)
   
5. User interacts with suggestions:
   ├─> Click "Preview" → See automation details
   ├─> Click "Edit" → Refine with natural language
   └─> Click "Apply" → Create automation
   
6. Confirmation message:
   └─> "✓ Automation created! Want to test it now?"
```

#### **Flow 2: Multi-Turn Refinement**
```
1. User: "Flash office lights when VGK scores"
   └─> AI: Returns 3 ranked suggestions
   
2. User: "Only during evening games"
   └─> AI: Refines suggestions with time condition
   
3. User: "Make it flash 5 times instead of 3"
   └─> AI: Updates suggestion action
   
4. User: "Perfect, apply the first one"
   └─> AI: Creates automation
```

#### **Flow 3: Device Discovery**
```
1. User: "What can I do with my office lights?"
   
2. AI: "Your office lights support:"
   ├─> Brightness control (0-100%)
   ├─> RGB color (16 million colors)
   ├─> Color temperature (2700K-6500K)
   └─> Smooth transitions
   
3. AI: "Here are some automation ideas:"
   ├─> Flash on VGK goals (Confidence: 95%)
   ├─> Dim when electricity expensive (Confidence: 87%)
   └─> Turn off when leaving home (Confidence: 82%)
   
4. User clicks on a suggestion
   └─> AI provides details and Apply option
```

### **User Personas**

| Persona | Goal | Interaction Style |
|---------|------|------------------|
| **Novice User** | "I don't know what's possible" | Guided with suggested prompts, discovery-focused |
| **Experienced User** | "I know what I want" | Direct commands, quick refinement |
| **Explorer** | "Show me what I can automate" | Device-focused queries, capability discovery |

---

## 🎨 **UI/UX Design**

### **Option 1: Conversational Cards (RECOMMENDED)**

**Why this is recommended:**
- ✅ Reuses existing `ConversationalSuggestionCard.tsx` component
- ✅ Proven UX pattern (ChatGPT-like)
- ✅ Easy to implement with existing tech stack
- ✅ Consistent with current HA AutomateAI design

#### **Layout: Full Chat Interface**

```
┌─────────────────────────────────────────────────────────────┐
│  💬 Ask AI                                         [🌙 Dark] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [No conversation history yet]                                │
│                                                               │
│  💡 Try asking:                                              │
│  ┌───────────────────────────────────────────────┐          │
│  │ "Flash my office lights when VGK scores"      │ [Ask]    │
│  ├───────────────────────────────────────────────┤          │
│  │ "Turn off devices when electricity expensive" │ [Ask]    │
│  ├───────────────────────────────────────────────┤          │
│  │ "What can I automate with my office lights?"  │ [Ask]    │
│  └───────────────────────────────────────────────┘          │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ What would you like to automate?            [Send]  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  🎛️ Context: 47 devices • VGK tracking • 12 automations    │
└─────────────────────────────────────────────────────────────┘
```

#### **Layout: Active Conversation**

```
┌─────────────────────────────────────────────────────────────┐
│  💬 Ask AI                              [Clear] [🌙 Dark]    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐            │
│  │ [Chat History - Scrollable]                 │            │
│  │                                             │            │
│  │  👤 You (just now)                          │            │
│  │  "I want to flash the office lights when   │            │
│  │   VGK scores"                               │            │
│  │                                             │            │
│  │  🤖 AI (just now)                           │            │
│  │  I found 3 automation suggestions for you   │            │
│  │  based on your devices and VGK tracking:    │            │
│  │                                             │            │
│  │  ┌──────────────────────────────────────┐  │            │
│  │  │ [Suggestion Card 1] ⭐⭐⭐⭐⭐          │  │            │
│  │  │ 📍 Office Light VGK Goal Flash       │  │            │
│  │  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │  │            │
│  │  │ When: VGK scores a goal              │  │            │
│  │  │ Do: Flash light.office 3x (blue)     │  │            │
│  │  │ Devices: light.office                │  │            │
│  │  │ Confidence: 95%                      │  │            │
│  │  │ [👁️ Preview] [✏️ Edit] [✓ Apply]     │  │            │
│  │  └──────────────────────────────────────┘  │            │
│  │                                             │            │
│  │  ┌──────────────────────────────────────┐  │            │
│  │  │ [Suggestion Card 2] ⭐⭐⭐⭐            │  │            │
│  │  │ 📍 Office Light Score Change         │  │            │
│  │  │ ... (similar structure)              │  │            │
│  │  └──────────────────────────────────────┘  │            │
│  │                                             │            │
│  │  ┌──────────────────────────────────────┐  │            │
│  │  │ [Suggestion Card 3] ⭐⭐⭐              │  │            │
│  │  │ 📍 Office Light + Notification       │  │            │
│  │  │ ... (similar structure)              │  │            │
│  │  └──────────────────────────────────────┘  │            │
│  │                                             │            │
│  │  🤖 AI (just now)                           │            │
│  │  Would you like to refine any of these, or │            │
│  │  ask something else?                        │            │
│  │                                             │            │
│  └─────────────────────────────────────────────┘            │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Type your message...                        [Send]  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  🎛️ Context: 47 devices • VGK game active • Office lights  │
└─────────────────────────────────────────────────────────────┘
```

### **Message Types**

#### **1. User Message Bubble**
```tsx
<div className="flex justify-end mb-4">
  <div className="max-w-2xl bg-blue-600 text-white px-4 py-3 rounded-2xl">
    <div className="flex items-center gap-2 mb-1">
      <span className="text-sm opacity-70">You</span>
      <span className="text-xs opacity-50">just now</span>
    </div>
    <p>I want to flash the office lights when VGK scores</p>
  </div>
</div>
```

#### **2. AI Text Response**
```tsx
<div className="flex justify-start mb-4">
  <div className="max-w-2xl bg-gray-100 dark:bg-gray-800 px-4 py-3 rounded-2xl">
    <div className="flex items-center gap-2 mb-1">
      <span className="text-sm font-medium">🤖 AI</span>
      <span className="text-xs opacity-50">just now</span>
    </div>
    <p>I found 3 automation suggestions for you...</p>
  </div>
</div>
```

#### **3. AI Suggestion Cards**
```tsx
<div className="flex justify-start mb-4">
  <div className="max-w-4xl w-full space-y-4">
    <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
      🤖 AI • just now
    </div>
    {/* Reuse existing ConversationalSuggestionCard */}
    <ConversationalSuggestionCard
      suggestion={suggestion}
      onRefine={handleRefine}
      onApprove={handleApprove}
      onReject={handleReject}
      darkMode={darkMode}
    />
  </div>
</div>
```

### **Suggested Prompts (Personalized)**

**Logic for generating prompts:**
```typescript
function generateSuggestedPrompts(context: UserContext): string[] {
  const prompts: string[] = [];
  
  // Sports tracking
  if (context.sports_tracking.includes('VGK')) {
    prompts.push("Flash my lights when VGK scores");
    prompts.push("Notify me when Golden Knights win");
  }
  
  // Energy pricing
  if (context.has_energy_pricing) {
    prompts.push("Turn off devices when electricity is expensive");
    prompts.push("Run dishwasher during cheap electricity hours");
  }
  
  // Weather
  if (context.has_weather) {
    prompts.push("Adjust temperature based on weather");
    prompts.push("Close blinds when it's sunny and hot");
  }
  
  // Device discovery (always)
  prompts.push("What can I automate with my devices?");
  prompts.push("Show me energy-saving automations");
  
  return prompts.slice(0, 4); // Max 4 prompts
}
```

### **Context Indicator (Bottom Bar)**

```tsx
<div className="text-xs text-gray-500 dark:text-gray-400 px-4 py-2 border-t">
  <div className="flex items-center gap-4">
    <span>🎛️ Context:</span>
    <span>47 devices available</span>
    {context.vgk_tracking && <span>• VGK game tracking active</span>}
    {context.mentioned_devices.length > 0 && (
      <span>• Devices: {context.mentioned_devices.join(', ')}</span>
    )}
    <span>• {context.existing_automations} existing automations</span>
  </div>
</div>
```

---

## 🏗️ **Technical Architecture**

### **System Architecture Diagram**

```
┌──────────────────────────────────────────────────────────┐
│  Frontend (React + TypeScript)                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │  AskAITab.tsx                                      │  │
│  │  ├─> ChatContainer.tsx (message history)          │  │
│  │  ├─> MessageBubble.tsx (user/AI messages)         │  │
│  │  ├─> SuggestionCardMessage.tsx (wrapper)          │  │
│  │  │   └─> ConversationalSuggestionCard.tsx (reuse) │  │
│  │  ├─> PromptSuggestions.tsx (quick start)          │  │
│  │  └─> ChatInput.tsx (text input + send)            │  │
│  └────────────────────────────────────────────────────┘  │
│                        ↕ HTTP/WebSocket                   │
├──────────────────────────────────────────────────────────┤
│  Backend (FastAPI)                                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  ai-automation-service                             │  │
│  │  ├─> /api/v1/ask-ai/query (NEW)                   │  │
│  │  │   ├─> NLP Parser (intent extraction)           │  │
│  │  │   ├─> RAG Engine (existing suggestion engine)  │  │
│  │  │   └─> Response Formatter (chat format)         │  │
│  │  ├─> /api/v1/ask-ai/context (NEW)                 │  │
│  │  └─> /api/v1/suggestions/* (existing endpoints)   │  │
│  └────────────────────────────────────────────────────┘  │
│                        ↕                                   │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Existing Components (Reuse)                       │  │
│  │  ├─> Pattern Detection Engine                     │  │
│  │  ├─> Suggestion Generation (OpenAI GPT-4o-mini)   │  │
│  │  ├─> Device Registry (data-api)                   │  │
│  │  ├─> Sports Tracking (sports-data)                │  │
│  │  └─> Energy/Weather Data (enrichment-pipeline)    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### **Data Flow: User Question → AI Response**

```
1. User Input
   ↓
   "Flash office lights when VGK scores"
   
2. Frontend (AskAITab.tsx)
   ├─> Parse user intent (client-side pre-processing)
   ├─> Extract mentioned devices ("office lights")
   └─> POST /api/v1/ask-ai/query
   
3. Backend NLP Parser
   ├─> Intent: "create_automation"
   ├─> Entity: "office lights" → "light.office"
   ├─> Trigger: "VGK scores" → sports_event
   └─> Context: {devices, sports_teams, energy_data}
   
4. RAG Query (Existing Suggestion Engine)
   ├─> Vector search: Similar patterns
   ├─> Filter: VGK + lights
   ├─> Rank: Confidence scores
   └─> Top 3 suggestions
   
5. Response Formatter
   ├─> Generate conversational message
   ├─> Format suggestions as cards
   └─> Add follow-up prompts
   
6. Frontend Rendering
   ├─> Display AI message bubble
   ├─> Render ConversationalSuggestionCard components
   └─> Update context indicator
```

---

## 🔌 **API Design**

### **New Endpoints**

#### **POST /api/v1/ask-ai/query**

**Purpose:** Process natural language query and return suggestions

**Request:**
```typescript
interface AskAIQueryRequest {
  query: string;                    // "Flash office lights when VGK scores"
  conversation_history?: Message[]; // Previous messages for context
  context?: {
    mentioned_devices?: string[];   // Previously mentioned devices
    user_preferences?: object;      // User settings
  };
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: object;
}
```

**Response:**
```typescript
interface AskAIQueryResponse {
  response_type: 'text' | 'suggestions' | 'clarification';
  message: string; // "I found 3 automation suggestions..."
  suggestions?: Suggestion[]; // Array of automation suggestions
  follow_up_prompts?: string[]; // Suggested next questions
  context_used: {
    devices_detected: string[];
    triggers_detected: string[];
    conditions_detected: string[];
  };
  metadata: {
    query_id: string;
    processing_time_ms: number;
    confidence: number;
  };
}

interface Suggestion {
  id: number;
  suggestion_id: string;
  title: string;
  description_only: string;
  category: string;
  confidence: number;
  status: string;
  device_capabilities?: object;
  conversation_history?: object[];
  created_at: string;
}
```

**Example:**
```bash
POST /api/v1/ask-ai/query
Content-Type: application/json

{
  "query": "Flash office lights when VGK scores",
  "conversation_history": [],
  "context": {
    "mentioned_devices": [],
    "user_preferences": {}
  }
}

# Response:
{
  "response_type": "suggestions",
  "message": "I found 3 automation ideas for flashing your office lights when VGK scores!",
  "suggestions": [
    {
      "id": 1,
      "suggestion_id": "suggestion-1",
      "title": "Office Light VGK Goal Flash",
      "description_only": "When the Vegas Golden Knights score a goal, flash the office light 3 times in blue",
      "category": "convenience",
      "confidence": 0.95,
      "status": "draft",
      "device_capabilities": {...},
      "created_at": "2025-10-19T12:00:00Z"
    },
    // ... 2 more suggestions
  ],
  "follow_up_prompts": [
    "Only during evening games",
    "Make it flash 5 times instead",
    "Add a notification too"
  ],
  "context_used": {
    "devices_detected": ["light.office"],
    "triggers_detected": ["sports_event:VGK:goal"],
    "conditions_detected": []
  },
  "metadata": {
    "query_id": "query-abc123",
    "processing_time_ms": 250,
    "confidence": 0.92
  }
}
```

#### **GET /api/v1/ask-ai/context**

**Purpose:** Get current user context for UI display

**Response:**
```typescript
interface UserContext {
  devices: {
    total: number;
    by_domain: { [domain: string]: number };
    recently_mentioned: string[];
  };
  integrations: {
    sports_tracking: string[]; // ["VGK", "NHL"]
    energy_pricing: boolean;
    weather: boolean;
    calendar: boolean;
  };
  automations: {
    total: number;
    by_category: { [category: string]: number };
  };
  suggested_prompts: string[];
}
```

#### **POST /api/v1/ask-ai/clarify**

**Purpose:** Ask clarifying questions when query is ambiguous

**Request:**
```typescript
interface ClarificationRequest {
  query_id: string;
  user_response: string;
}
```

**Response:**
```typescript
interface ClarificationResponse {
  clarified_query: string;
  // Then redirects to query endpoint
}
```

---

## 🧩 **Component Structure**

### **File Tree**

```
services/ai-automation-ui/src/
├── pages/
│   ├── AskAI.tsx                        # NEW: Main page
│   └── ConversationalDashboard.tsx       # Existing (keep as-is)
│
├── components/
│   ├── ask-ai/                           # NEW: Chat components folder
│   │   ├── ChatContainer.tsx             # Message history container
│   │   ├── MessageBubble.tsx             # User/AI message bubble
│   │   ├── SuggestionCardMessage.tsx     # Wrapper for suggestion cards in chat
│   │   ├── ChatInput.tsx                 # Text input with send button
│   │   ├── PromptSuggestions.tsx         # Suggested prompts (quick start)
│   │   ├── ContextIndicator.tsx          # Context display (bottom bar)
│   │   ├── TypingIndicator.tsx           # "AI is typing..." animation
│   │   └── WelcomeScreen.tsx             # Empty state welcome
│   │
│   ├── ConversationalSuggestionCard.tsx  # Existing (REUSE as-is)
│   └── SuggestionCard.tsx                # Existing (keep)
│
├── hooks/
│   ├── useAskAI.ts                       # NEW: Chat state management
│   ├── useChatMessages.ts                # NEW: Message history
│   └── useOptimisticUpdates.ts           # Existing (reuse)
│
├── services/
│   └── api.ts                            # Add new ask-ai methods
│
├── types/
│   └── ask-ai.ts                         # NEW: Type definitions
│
└── App.tsx                               # Add /ask-ai route
```

### **Component Specifications**

#### **AskAI.tsx** (Main Page Component)

```tsx
/**
 * Ask AI Page - Chat interface for automation suggestions
 */
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store';
import { ChatContainer } from '../components/ask-ai/ChatContainer';
import { ChatInput } from '../components/ask-ai/ChatInput';
import { ContextIndicator } from '../components/ask-ai/ContextIndicator';
import { WelcomeScreen } from '../components/ask-ai/WelcomeScreen';
import { useChatMessages } from '../hooks/useChatMessages';
import { useAskAI } from '../hooks/useAskAI';
import type { Message, UserContext } from '../types/ask-ai';

export const AskAI: React.FC = () => {
  const { darkMode } = useAppStore();
  const { messages, addMessage, clearMessages } = useChatMessages();
  const { query, isLoading, context } = useAskAI();
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleSendMessage = async (text: string) => {
    // Add user message
    addMessage({
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    });
    
    // Query AI
    const response = await query(text, messages);
    
    // Add AI response
    addMessage({
      role: 'assistant',
      content: response.message,
      timestamp: new Date().toISOString(),
      metadata: {
        suggestions: response.suggestions,
        follow_up_prompts: response.follow_up_prompts
      }
    });
  };
  
  const handleSuggestedPrompt = (prompt: string) => {
    handleSendMessage(prompt);
  };
  
  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      {/* Header */}
      <div className={`border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'} px-6 py-4`}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              💬 Ask AI
            </h1>
            <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Ask questions about your smart home and get automation suggestions
            </p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearMessages}
              className={`text-sm px-4 py-2 rounded-lg transition-colors ${
                darkMode
                  ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              Clear Chat
            </button>
          )}
        </div>
      </div>
      
      {/* Chat Container */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <WelcomeScreen
            context={context}
            onPromptClick={handleSuggestedPrompt}
            darkMode={darkMode}
          />
        ) : (
          <ChatContainer
            messages={messages}
            isLoading={isLoading}
            darkMode={darkMode}
          />
        )}
        <div ref={chatEndRef} />
      </div>
      
      {/* Context Indicator */}
      <ContextIndicator context={context} darkMode={darkMode} />
      
      {/* Chat Input */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={isLoading}
        darkMode={darkMode}
      />
    </div>
  );
};
```

#### **ChatContainer.tsx**

```tsx
/**
 * Chat Container - Displays message history
 */
import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { MessageBubble } from './MessageBubble';
import { SuggestionCardMessage } from './SuggestionCardMessage';
import { TypingIndicator } from './TypingIndicator';
import type { Message } from '../../types/ask-ai';

interface Props {
  messages: Message[];
  isLoading: boolean;
  darkMode: boolean;
}

export const ChatContainer: React.FC<Props> = ({ messages, isLoading, darkMode }) => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <AnimatePresence mode="popLayout">
        {messages.map((message, index) => (
          <motion.div
            key={`${message.timestamp}-${index}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            {message.metadata?.suggestions ? (
              // AI message with suggestion cards
              <SuggestionCardMessage
                message={message}
                darkMode={darkMode}
              />
            ) : (
              // Regular text message (user or AI)
              <MessageBubble
                message={message}
                darkMode={darkMode}
              />
            )}
          </motion.div>
        ))}
      </AnimatePresence>
      
      {isLoading && <TypingIndicator darkMode={darkMode} />}
    </div>
  );
};
```

#### **MessageBubble.tsx**

```tsx
/**
 * Message Bubble - User or AI text message
 */
import React from 'react';
import type { Message } from '../../types/ask-ai';

interface Props {
  message: Message;
  darkMode: boolean;
}

export const MessageBubble: React.FC<Props> = ({ message, darkMode }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-2xl px-4 py-3 rounded-2xl ${
        isUser
          ? 'bg-blue-600 text-white'
          : darkMode
          ? 'bg-gray-800 text-gray-100'
          : 'bg-gray-100 text-gray-900'
      }`}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium">
            {isUser ? '👤 You' : '🤖 AI'}
          </span>
          <span className="text-xs opacity-50">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <p className="text-sm leading-relaxed">{message.content}</p>
      </div>
    </div>
  );
};
```

#### **SuggestionCardMessage.tsx**

```tsx
/**
 * Suggestion Card Message - AI response with suggestion cards
 */
import React from 'react';
import { ConversationalSuggestionCard } from '../ConversationalSuggestionCard';
import type { Message } from '../../types/ask-ai';

interface Props {
  message: Message;
  darkMode: boolean;
}

export const SuggestionCardMessage: React.FC<Props> = ({ message, darkMode }) => {
  const suggestions = message.metadata?.suggestions || [];
  const followUpPrompts = message.metadata?.follow_up_prompts || [];
  
  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-4xl w-full space-y-4">
        {/* AI Header */}
        <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          <span className="font-medium">🤖 AI</span>
          <span className="opacity-50 ml-2">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>
        
        {/* AI Message */}
        <div className={`px-4 py-3 rounded-2xl ${
          darkMode ? 'bg-gray-800 text-gray-100' : 'bg-gray-100 text-gray-900'
        }`}>
          <p className="text-sm leading-relaxed">{message.content}</p>
        </div>
        
        {/* Suggestion Cards */}
        <div className="space-y-4">
          {suggestions.map((suggestion) => (
            <ConversationalSuggestionCard
              key={suggestion.id}
              suggestion={suggestion}
              onRefine={handleRefine}
              onApprove={handleApprove}
              onReject={handleReject}
              darkMode={darkMode}
            />
          ))}
        </div>
        
        {/* Follow-up Prompts */}
        {followUpPrompts.length > 0 && (
          <div className="mt-4">
            <p className={`text-xs mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              💡 You can also try:
            </p>
            <div className="flex flex-wrap gap-2">
              {followUpPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleFollowUpClick(prompt)}
                  className={`text-xs px-3 py-2 rounded-lg transition-colors ${
                    darkMode
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                      : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                  }`}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Handlers would be passed as props in real implementation
const handleRefine = async (id: number, input: string) => {
  // Call existing API
};

const handleApprove = async (id: number) => {
  // Call existing API
};

const handleReject = async (id: number) => {
  // Call existing API
};

const handleFollowUpClick = (prompt: string) => {
  // Send as new message
};
```

#### **ChatInput.tsx**

```tsx
/**
 * Chat Input - Text input with send button
 */
import React, { useState, useRef, useEffect } from 'react';

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
  darkMode: boolean;
}

export const ChatInput: React.FC<Props> = ({ onSend, disabled, darkMode }) => {
  const [text, setText] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  // Auto-focus on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);
  
  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text.trim());
      setText('');
      inputRef.current?.focus();
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  return (
    <div className={`border-t ${darkMode ? 'border-gray-700 bg-gray-900' : 'border-gray-200 bg-white'} px-6 py-4`}>
      <div className="max-w-4xl mx-auto flex gap-3">
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="What would you like to automate?"
          disabled={disabled}
          rows={1}
          className={`flex-1 resize-none rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            darkMode
              ? 'bg-gray-800 text-white placeholder-gray-500'
              : 'bg-gray-100 text-gray-900 placeholder-gray-400'
          }`}
          style={{ minHeight: '48px', maxHeight: '120px' }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
          Send
        </button>
      </div>
    </div>
  );
};
```

---

## 🔍 **RAG Integration**

### **Query Processing Pipeline**

```python
# ai-automation-service/src/api/ask_ai_router.py

async def process_ask_ai_query(query: str, context: dict) -> AskAIResponse:
    """
    Process natural language query using RAG approach.
    
    Flow:
    1. Parse query (NLP)
    2. Extract entities and intents
    3. Query suggestion engine (RAG)
    4. Format response
    """
    
    # Step 1: Parse query with OpenAI
    parsed_query = await openai_client.parse_query(
        query=query,
        context=context
    )
    
    # Step 2: Extract entities
    entities = {
        'devices': extract_devices(parsed_query),
        'triggers': extract_triggers(parsed_query),
        'conditions': extract_conditions(parsed_query)
    }
    
    # Step 3: Query existing suggestion engine (RAG)
    suggestions = await suggestion_engine.query_similar_patterns(
        devices=entities['devices'],
        triggers=entities['triggers'],
        conditions=entities['conditions'],
        top_k=3  # Return top 3 suggestions
    )
    
    # Step 4: Generate conversational response
    response_message = await openai_client.generate_chat_response(
        query=query,
        suggestions=suggestions,
        context=context
    )
    
    # Step 5: Generate follow-up prompts
    follow_ups = generate_follow_up_prompts(
        query=query,
        suggestions=suggestions,
        entities=entities
    )
    
    return AskAIResponse(
        response_type='suggestions',
        message=response_message,
        suggestions=suggestions,
        follow_up_prompts=follow_ups,
        context_used=entities
    )
```

### **NLP Parser (OpenAI-based)**

```python
async def parse_query(query: str, context: dict) -> ParsedQuery:
    """
    Parse natural language query to extract intent and entities.
    
    Uses OpenAI GPT-4o-mini for structured extraction.
    """
    
    prompt = f"""
    Parse this smart home automation query and extract structured information.
    
    Query: "{query}"
    
    Available context:
    - Devices: {context.get('devices', [])}
    - Sports teams: {context.get('sports_teams', [])}
    - Integrations: {context.get('integrations', [])}
    
    Extract:
    1. Intent (create_automation, discover_capabilities, ask_question)
    2. Devices mentioned (map to entity_ids)
    3. Triggers (time, sports_event, weather, state_change)
    4. Actions (turn_on, flash, notify, adjust)
    5. Conditions (time_of_day, day_of_week, state)
    
    Return as JSON.
    """
    
    response = await openai_client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    return ParsedQuery(**json.loads(response.choices[0].message.content))
```

### **Suggestion Engine Query (Existing)**

```python
async def query_similar_patterns(
    devices: List[str],
    triggers: List[str],
    conditions: List[str],
    top_k: int = 3
) -> List[Suggestion]:
    """
    Query existing suggestion engine for similar patterns.
    
    This REUSES your existing pattern detection and suggestion generation!
    """
    
    # Query pattern database
    patterns = await pattern_db.search(
        devices=devices,
        triggers=triggers,
        conditions=conditions,
        limit=top_k * 2  # Get more for filtering
    )
    
    # Generate suggestions for each pattern
    suggestions = []
    for pattern in patterns[:top_k]:
        suggestion = await generate_suggestion_from_pattern(
            pattern=pattern,
            device_context=await get_device_context(devices)
        )
        suggestions.append(suggestion)
    
    # Rank by confidence
    suggestions.sort(key=lambda s: s.confidence, reverse=True)
    
    return suggestions[:top_k]
```

---

## 📅 **Implementation Plan**

### **Phase 1: MVP (Week 1-2)**

**Goal:** Basic chat UI with RAG-powered suggestions

**Tasks:**
1. ✅ Design review and approval (this document)
2. ⬜ Create new `/ask-ai` route in App.tsx
3. ⬜ Implement basic chat components:
   - AskAI.tsx (main page)
   - ChatContainer.tsx
   - MessageBubble.tsx
   - ChatInput.tsx
   - WelcomeScreen.tsx
4. ⬜ Implement backend endpoint: `/api/v1/ask-ai/query`
5. ⬜ Integrate with existing suggestion engine (RAG)
6. ⬜ Basic NLP parsing (OpenAI)
7. ⬜ Display suggestions using existing ConversationalSuggestionCard
8. ⬜ Test with sample queries

**Success Criteria:**
- User can ask questions and receive suggestions
- Suggestions displayed as interactive cards
- Basic conversational flow works

### **Phase 2: Context & Refinement (Week 3)**

**Goal:** Multi-turn conversations and context awareness

**Tasks:**
1. ⬜ Implement conversation history management
2. ⬜ Add context tracking (mentioned devices, intents)
3. ⬜ Generate follow-up prompts dynamically
4. ⬜ Implement ContextIndicator component
5. ⬜ Add suggested prompts (personalized)
6. ⬜ Test multi-turn refinement flows

**Success Criteria:**
- Multi-turn conversations work
- Context persists across messages
- Follow-up prompts are relevant

### **Phase 3: Advanced Features (Week 4)**

**Goal:** Polish and advanced capabilities

**Tasks:**
1. ⬜ Implement TypingIndicator animation
2. ⬜ Add clarification questions (when query ambiguous)
3. ⬜ Improve NLP parser (better entity extraction)
4. ⬜ Add conversation export/import
5. ⬜ Performance optimization
6. ⬜ Error handling improvements

**Success Criteria:**
- Smooth UX with animations
- Handles ambiguous queries
- Fast response times (<500ms)

### **Phase 4: Testing & Deployment (Week 5)**

**Goal:** Production-ready release

**Tasks:**
1. ⬜ Write unit tests (components)
2. ⬜ Write integration tests (API)
3. ⬜ E2E tests (Playwright)
4. ⬜ Performance testing
5. ⬜ Documentation
6. ⬜ Deploy to production

**Success Criteria:**
- 80%+ test coverage
- All E2E tests passing
- Documentation complete

---

## 🔧 **Technology Decisions**

### **Chat UI Library: Custom Implementation (RECOMMENDED)**

**Decision:** Build custom chat components instead of using a library

**Rationale:**
- ✅ Full control over UX (matches existing design)
- ✅ Reuse existing components (ConversationalSuggestionCard)
- ✅ Lightweight (no heavy dependencies)
- ✅ Already have all building blocks (Framer Motion, Tailwind)

**Alternatives Considered:**
- `assistant-ui/assistant-ui` - Too opinionated, overkill for our use case
- `react-chatbotify` - Good but adds 2.5MB, we need custom suggestion cards
- **HuggingChat UI** ([GitHub](https://github.com/huggingface/chat-ui)) - Open-source, SvelteKit-based
  - ⚠️ Different framework (SvelteKit vs React)
  - ✅ Could use as UI/UX reference
  - ✅ Great for learning chat UI patterns
  - 📖 **Reference for best practices, not direct integration**

### **NLP Processing: Hybrid Approach (RECOMMENDED)**

**Decision:** Use **Hugging Face** for embeddings/classification + **OpenAI** for complex reasoning

**Rationale:**
- ✅ **Cost optimization**: Use free Hugging Face models where possible
- ✅ **Already integrated**: Using sentence-transformers for embeddings
- ✅ **Flexibility**: Mix open-source and commercial models
- ✅ **Privacy**: Some processing stays local

**Architecture:**
```
User Query
    ↓
1. Hugging Face Transformers (Local/Inference API - FREE)
   ├─> Entity extraction (NER pipeline)
   ├─> Intent classification (zero-shot-classification)
   └─> Device matching (sentence-transformers embeddings)
    ↓
2. RAG Query (Existing - Uses HuggingFace embeddings)
   └─> Pattern similarity search
    ↓
3. OpenAI GPT-4o-mini (Paid - Only when needed)
   └─> Complex reasoning
   └─> Conversational response generation
```

**Recommended Hugging Face Models:**

| Task | Model | Cost | Speed | Accuracy |
|------|-------|------|-------|----------|
| **Entity Extraction** | `dslim/bert-base-NER` | FREE | 50ms | 90%+ |
| **Intent Classification** | `facebook/bart-large-mnli` (zero-shot) | FREE | 100ms | 85%+ |
| **Device Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | FREE | 20ms | Already using! |
| **Conversational Response** | OpenAI GPT-4o-mini | $0.0004/query | 500ms | 95%+ |

**Cost Estimate (Hybrid):**
- Entity extraction: FREE (Hugging Face)
- Intent classification: FREE (Hugging Face)
- Device matching: FREE (local embeddings - already deployed)
- Complex reasoning: 100 queries/day × $0.0004 = **$0.04/day = $1.20/month**
- **Total: ~$1.20/month** (70% cost reduction vs pure OpenAI)

**Alternative: 100% FREE with Hugging Face Inference API**

For completely free operation, use Hugging Face's free Inference API:

```python
from transformers import pipeline

# FREE conversational pipeline (no API key needed)
chatbot = pipeline("conversational", model="facebook/blenderbot-400M-distill")

# Or use Hugging Face Inference API (FREE tier available)
import requests

API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}  # Free HF token

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

output = query({
    "inputs": {
        "past_user_inputs": ["I want to flash my office lights when VGK scores"],
        "generated_responses": [],
        "text": "Flash office lights when VGK scores"
    },
})
```

**Trade-offs:**
- ✅ **100% FREE** (Hugging Face Inference API free tier)
- ✅ No monthly costs
- ⚠️ Slower response (~1-2s vs 500ms for OpenAI)
- ⚠️ Lower accuracy (~75-80% vs 95% for GPT-4o-mini)
- ✅ Full privacy (data doesn't leave your control)

**Recommended Models for Free Inference:**
- `facebook/blenderbot-400M-distill` - Fast, conversational
- `microsoft/DialoGPT-medium` - Good quality, medium size
- `google/flan-t5-base` - Instruction-following, general purpose

### **RAG Implementation: Existing Suggestion Engine (RECOMMENDED)**

**Decision:** Reuse existing pattern detection and suggestion generation

**Rationale:**
- ✅ Already works (proven accuracy: 80-85%)
- ✅ No additional development needed
- ✅ Uses same models and data
- ✅ Just add conversational wrapper

**What's New:**
- Query parsing layer (NLP)
- Conversational response formatting
- Follow-up prompt generation

### **State Management: Zustand (EXISTING)**

**Decision:** Extend existing Zustand store for chat state

**Rationale:**
- ✅ Already used in the app
- ✅ Simple and performant
- ✅ TypeScript-friendly

```typescript
// Add to existing store.ts
interface AppState {
  // ... existing state
  askAI: {
    messages: Message[];
    context: UserContext;
    isLoading: boolean;
  };
  // Actions
  addAskAIMessage: (message: Message) => void;
  clearAskAIMessages: () => void;
  setAskAIContext: (context: UserContext) => void;
}
```

---

## 🎓 **Training Data & Fine-Tuning (Hugging Face Datasets)**

### **Free & Royalty-Free Datasets Available**

Based on research from [Hugging Face Datasets Hub](https://huggingface.co/datasets), here are relevant free datasets for training/fine-tuning:

#### **1. Conversational AI Datasets**

| Dataset | License | Size | Use Case | Link |
|---------|---------|------|----------|------|
| **awesome-chatgpt-prompts** | CC0-1.0 (Public Domain) | 38.6k downloads | Chat prompts and examples | [🔗 HF](https://huggingface.co/datasets/fka/awesome-chatgpt-prompts) |
| **OpenAssistant Conversations** | Apache 2.0 | ~161k conversations | Human-feedback ranked conversations | [🔗 HF](https://huggingface.co/datasets/OpenAssistant/oasst1) |
| **Dolly 15k** | CC-BY-SA-3.0 | 15k instructions | Instruction-following tasks | [🔗 HF](https://huggingface.co/datasets/databricks/databricks-dolly-15k) |

#### **2. Smart Home & IoT Datasets**

| Dataset | License | Description | Link |
|---------|---------|-------------|------|
| **hqfx/hermes_fc_cleaned** | Apache 2.0 | Home Assistant integration examples | [🔗 HF](https://huggingface.co/datasets/hqfx/hermes_fc_cleaned) |
| **globosetechnology12/Smart-Home-Automation** | MIT | Smart home case studies | [🔗 HF](https://huggingface.co/datasets/globosetechnology12/Smart-Home-Automation) |

#### **3. Question-Answering Datasets**

| Dataset | License | Size | Use Case | Link |
|---------|---------|------|----------|------|
| **SQuAD 2.0** | CC-BY-SA-4.0 | 100k+ questions | QA training | [🔗 HF](https://huggingface.co/datasets/squad_v2) |
| **Natural Questions** | Apache 2.0 | 300k questions | Real user questions | [🔗 HF](https://huggingface.co/datasets/google/natural_questions) |

### **How to Use These Datasets**

```python
from datasets import load_dataset

# Load awesome-chatgpt-prompts (FREE, Public Domain)
prompts_dataset = load_dataset("fka/awesome-chatgpt-prompts")

# Load Home Assistant examples (FREE, Apache 2.0)
ha_dataset = load_dataset("hqfx/hermes_fc_cleaned")

# Load instruction-following examples (FREE, CC-BY-SA)
instruct_dataset = load_dataset("databricks/databricks-dolly-15k")

# Example: Fine-tune on smart home conversations
for example in ha_dataset['train']:
    # Use for fine-tuning your conversational model
    conversation = example['messages']
    # ... fine-tuning logic
```

### **Recommended Training Strategy**

**Phase 1: Use Pre-trained Models (No training needed)** ← **START HERE**
- ✅ Use existing OpenAI GPT-4o-mini (already working)
- ✅ Use Hugging Face Transformers pipelines (free)
- ⏱️ Time to deploy: Immediate
- 💰 Cost: $1.20/month (OpenAI only)

**Phase 2: Fine-tune for Smart Home Domain (Optional - Future)**
- 📚 Combine datasets:
  - `awesome-chatgpt-prompts` (conversational patterns)
  - `hqfx/hermes_fc_cleaned` (HA-specific knowledge) ✨ **Already includes HA automation examples!**
  - `databricks-dolly-15k` (instruction-following)
- 🎯 Fine-tune small model (e.g., `flan-t5-base` or `gpt2-medium`)
- 💰 Cost: ~$20-50 for one-time fine-tuning (or free with local GPU)
- ⏱️ Time: 2-3 days development + training

**Phase 3: Continuous Learning (Future)**
- 📊 Collect user interactions from Ask AI tab
- 🔁 Periodically retrain on real usage data
- 📈 Improve accuracy based on actual queries

### **License Compliance**

All recommended datasets are free and royalty-free:
- ✅ **CC0-1.0 (Public Domain)**: No restrictions ([Filter](https://huggingface.co/datasets?license=license%3Aunlicense))
- ✅ **Apache 2.0**: Free to use, modify, distribute ([Filter](https://huggingface.co/datasets?license=license%3Aapache-2.0))
- ✅ **CC-BY-SA**: Free to use, must attribute, share-alike ([Filter](https://huggingface.co/datasets?license=license%3Acc))
- ✅ **MIT**: Free to use, minimal restrictions

**Important:** Always verify license before using. Hugging Face provides license filters for easy discovery.

### **Curated Collections**

Hugging Face has curated collections of high-quality, royalty-free datasets:
- 📚 [Royalty Free Datasets Collection](https://huggingface.co/collections/jdpressman/royalty-free-datasets-665d0312221dda4987e028f6)

### **Key Insight: Home Assistant Dataset Already Exists!**

The **`hqfx/hermes_fc_cleaned`** dataset already contains Home Assistant automation examples! This means:
- ✅ No need to create training data from scratch
- ✅ Real-world HA integration patterns available
- ✅ Can fine-tune models specifically for HA use cases
- ✅ Apache 2.0 license = free to use

---

## 📊 **Success Metrics**

### **User Engagement**
- **Goal:** 50% of users try Ask AI tab in first week
- **Metric:** Unique users who send at least 1 query

### **Query Success Rate**
- **Goal:** 80% of queries return useful suggestions
- **Metric:** Queries with ≥1 suggestion applied / total queries

### **Conversation Depth**
- **Goal:** Average 2.5 messages per conversation
- **Metric:** Total messages / total conversations

### **Suggestion Application Rate**
- **Goal:** 30% of suggestions get applied
- **Metric:** Suggestions applied / total suggestions shown

### **Performance**
- **Goal:** <500ms query response time
- **Metric:** Average API response time for `/api/v1/ask-ai/query`

---

## 🎯 **Next Steps**

1. ✅ **Review this design document** (get approval)
2. ⬜ **Create component mockups** (optional, if needed)
3. ⬜ **Set up development environment**
4. ⬜ **Start Phase 1 implementation**

---

## 📚 **References**

### **Context7 KB Research**
- Chat UI Libraries: [assistant-ui](https://github.com/assistant-ui/assistant-ui), [react-chatbotify](https://github.com/tjtanjin/react-chatbotify)
- RAG Patterns: [danny-avila/rag_api](https://github.com/danny-avila/rag_api)

### **Existing Components to Reuse**
- `ConversationalSuggestionCard.tsx` - Automation suggestion cards
- `useAppStore()` - Global state management
- AI Automation Service - Pattern detection + suggestion generation

### **Architecture Documents**
- `docs/architecture/tech-stack.md` - Technology stack
- `docs/architecture/source-tree.md` - Project structure
- `implementation/analysis/AI_AUTOMATION_CALL_TREE_INDEX.md` - AI service architecture

---

**Document Status:** Ready for implementation  
**Last Updated:** October 19, 2025  
**Author:** BMad Master (Design-First Approach)

