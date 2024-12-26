# Content Marketing Framework

## Overview
Content Marketing is 80% of Invisible Decisions - a hierarchical framework showing the strategic layers behind successful content marketing.

## Core Principle
The framework emphasizes that successful content marketing isn't just about creating content - it's about having a comprehensive strategy that aligns with business goals and target audience needs. The visible content (20%) is supported by invisible strategic decisions (80%).

## Framework Diagram

```mermaid
graph TB
    Start([1- Solution/Problem Discovery])
    
    subgraph BS["Business Strategy"]
        TA[2- Target Audience Analysis]
        VP[3- Value Proposition Development]
        BV[4- Brand Vision Formation]
        BSS[5- Business Strategy Synthesis]
        
        TA --> VP
        TA & VP --> BV
        TA & VP & BV --> BSS
    end
    
    subgraph MS["Marketing Strategy"]
        MSF[6- Marketing Strategy Formation]
        OF[7-. Offer Design]
        PO[7-. Positioning]
        USP[7-. USP Definition]
        MSG[7-. Messaging Framework]
        
        MSF --> OF --> PO --> USP --> MSG
    end
    
    subgraph CS["Content Strategy"]
        CSF[8- Content Strategy]
        MF[9-. Manifesto]
        NR[9-. Narrative]
        CP[9-. Content Pillars]
        POV[9-. Point of View]
        EN[9-. Enemy]
        
        CSF --> MF & NR & CP & POV & EN
    end
    
    subgraph CPL["Content Plan"]
        CPF[10- Content Plan Formation]
        CH[11a- Channels]
        FM[11b- Formats]
        DI[11c- Distribution]
        RP[11d- Repurposing]
        TL[11e- Timeline]
        
        CPF --> CH & FM & DI & RP & TL
    end
    
    subgraph EX["Content Execution"]
        CT[12- Content Creation]
        CW[13a- Copywriting]
        DS[13b- Design]
        VD[13c- Videos]
        PG[13d- Pages]
        SC[13e- Socials]
        TM[14- Target Market Reach]
        
        CT --> CW & DS & VD & PG & SC
        CW & DS & VD & PG & SC --> TM
    end
    
    Start --> TA
    BSS --> MSF
    MSG --> CSF
    EN --> CPF
    TL --> CT
    
    %% Feedback Loops to Business Strategy
    TM -.-|"feedback"| BS
    TM -.-|"feedback"| MS
    TM -.-|"feedback"| CS
    TM -.-|"feedback"| CPL
    
    %% New Feedback Loops to Solution/Problem Discovery
    BSS -.-|"strategy feedback"| Start
    MSG -.-|"market feedback"| Start
    EN -.-|"content feedback"| Start
    TM -.-|"execution feedback"| Start
    
    classDef strategy fill:#e6f3ff,stroke:#4a90e2
    classDef marketing fill:#fff3e6,stroke:#f5a623
    classDef content fill:#e6ffe6,stroke:#7ed321
    classDef execution fill:#ffe6e6,stroke:#d0021b
    
    class BS,TA,VP,BV,BSS strategy
    class MS,MSF,OF,PO,USP,MSG marketing
    class CS,CSF,MF,NR,CP,POV,EN content
    class CPL,CPF,CH,FM,DI,RP,TL content
    class EX,CT,CW,DS,VD,PG,SC,TM execution
```

## Framework Layers

### 1. Business Strategy Foundation
#### Target Audience Analysis
Identifying who you're trying to reach. Create detailed buyer personas including:

  - Demographics and psychographics
  - Pain points and challenges
  - Goals and aspirations
  - Preferred communication channels
  - Decision-making factors

#### Value Proposition Development
What unique value you offer. Core value statement addressing:
  - Problem solved
  - Benefits delivered
  - Competitive advantage
  - Success metrics

#### Brand Vision Statement
Your long-term brand direction and goals. Define:
  - 5-year vision
  - Core values
  - Brand personality
  - Market position aspiration

### 2. Marketing Strategy Framework
#### Offer Structure
What you're selling or providing.

- Primary offerings
- Pricing strategy
- Service/product bundles
- Customer journey touchpoints

#### Market Positioning
 How you position yourself in the market

- Competitive analysis
- Market gap identification
- Position statement
- Key differentiators

#### Unique Selling Proposition (USP)
What makes you different

- Primary USP
- Supporting evidence
- Competitive advantages
- Value metrics

#### Messaging Framework
How you communicate your value.

- Key messages by audience segment
- Tone of voice guidelines
- Brand language parameters
- Communication hierarchy

### 3. Content Strategy Blueprint
#### Brand Manifesto
Your core beliefs and principles

- Purpose statement
- Brand beliefs
- Industry stance
- Cultural impact

#### Brand Narrative
The story you tell

- Origin story
- Mission narrative
- Customer success stories
- Future vision

#### Content Pillars
Main themes or topics you focus on

- 3-5 core themes
- Sub-topics for each pillar
- Content mix ratios
- Expert positioning areas

#### Point of View Development
Your unique perspective

- Industry perspective
- Thought leadership areas
- Stance on key issues
- Innovation vision

#### Enemy Identification
What you're fighting against or trying to solve.

- Market problems to solve
- Industry pain points
- Competitive alternatives
- Status quo challenges

### 4. Content Planning System
#### Channel Strategy
Where you'll publish

- Primary channels
- Channel-specific goals
- Performance metrics
- Cross-channel integration

#### Content Formats
Types of content you'll create

- Format types by channel
- Production requirements
- Resource allocation
- Quality standards

#### Distribution Strategy
How you'll share your content

- Publishing calendar
- Promotion tactics
- Amplification methods
- Partnership opportunities

#### Repurposing Matrix
How you'll adapt content for different uses

- Content transformation map
- Cross-channel adaptation
- Update schedule
- Archive strategy

#### Timeline Management
When you'll publish

- Content calendar
- Production deadlines
- Review cycles
- Publication schedule

### 5. Content Creation & Execution
#### Copywriting Guidelines
The actual written content

- Style guide
- Voice and tone
- SEO requirements
- Call-to-action framework

#### Design Standards
- Visual identity guide
- Image guidelines
- Typography rules
- Brand colors

#### Video Production
- Video types
- Production standards
- Platform requirements
- Distribution plan

#### Page Development
- Website architecture
- Landing page templates
- Content organization
- User experience guidelines

#### Social Media Execution
- Platform-specific strategies
- Content types by platform
- Engagement guidelines
- Community management plan

## Success Metrics
- Engagement rates
- Conversion metrics
- Brand awareness
- Lead generation
- ROI measurements

## Framework Success Criteria
1. **Strategic Alignment**
   - All content aligns with business objectives
   - Clear connection between strategy and execution
   - Consistent messaging across channels

2. **Content Effectiveness**
   - Measurable engagement metrics
   - Achievement of conversion goals
   - Brand awareness growth
   - Lead generation success
   - Positive ROI measurements

3. **Process Efficiency**
   - Streamlined content production
   - Effective resource utilization
   - Consistent quality standards
   - Timely content delivery
