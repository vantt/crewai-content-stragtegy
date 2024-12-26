```mermaid
graph TB
    subgraph PSD["1- Problem/Solution Discovery"]
        Start([Discovery Process])
        MIR[Market Report<br/>- Customer Insight<br/>- Solution Validation Data<br/>- Recommendations & Findings]        
        Start --> MIR
    end
    
    subgraph BS["Business Strategy"]
        BSS[Business Strategy Document<br/>- Target Audience<br/>- Value Proposition<br/>- Brand Vision]
    end
    
    subgraph MS["Marketing Strategy"]
        MSF[Marketing Plan<br/>- Offer Design<br/>- Positioning<br/>- Messaging]
    end
    
    subgraph CS["Content Strategy"]
        CSF[Content Guidelines<br/>- Narrative<br/>- Pillars<br/>- Voice]
    end
    
    subgraph CPL["Content Plan"]
        CPF[Content Calendar<br/>- Channels<br/>- Formats<br/>- Timeline]
    end
    
    subgraph EX["Content Execution"]
        TM[Market Reach<br/>- Content Assets<br/>- Distribution<br/>- Performance]
    end
    
    MIR --> BSS
    BSS --> MSF
    MSF --> CSF
    CSF --> CPF
    CPF --> TM
    
    %% Feedback Loops
    TM -.-|"performance feedback"| BS
    TM -.-|"market feedback"| MS
    TM -.-|"content feedback"| CS
    TM -.-|"planning feedback"| CPL
    
    %% Strategic Feedback to Discovery
    BSS -.-|"strategy insights"| PSD
    MSF -.-|"market insights"| PSD
    CSF -.-|"content insights"| PSD
    TM -.-|"execution insights"| PSD
    
    classDef strategy fill:#e6f3ff,stroke:#4a90e2
    classDef marketing fill:#fff3e6,stroke:#f5a623
    classDef content fill:#e6ffe6,stroke:#7ed321
    classDef execution fill:#ffe6e6,stroke:#d0021b
    classDef discovery fill:#f0f0f0,stroke:#666666
    
    class BS,BSS strategy
    class MS,MSF marketing
    class CS,CSF content
    class CPL,CPF content
    class EX,TM execution
    class PSD,Start,DD,MIR,CID,SVD,RF discovery
```