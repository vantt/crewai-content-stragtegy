# Level 1: Business Strategy
```yaml
business_strategy:
  target_audience:
    personas:
      - id: string
        name: string
        demographics:
          age_range: string
          location: string
          income_level: string
          education: string
        psychographics:
          pain_points: [string]
          interests: [string]
          goals: [string]
        behavior:
          preferred_channels: [string]
          decision_factors: [string]
    
  value_proposition:
    problem_statement: string
    solution: string
    benefits: [string]
    proof_points: [string]
    success_metrics:
      - metric: string
        target: number
        timeframe: string
    
  brand_vision:
    mission: string
    values: [string]
    personality_traits: [string]
    five_year_goals: [string]
```

# Level 2: Marketing Strategy

```yaml
marketing_strategy:
  offer:
    products: [
      {
        name: string,
        description: string,
        price_point: number,
        target_segment: string
      }
    ]
    bundles: [
      {
        name: string,
        components: [string],
        value_add: string
      }
    ]
    
  positioning:
    market_segment: string
    competitors: [
      {
        name: string,
        strengths: [string],
        weaknesses: [string]
      }
    ]
    differentiators: [string]
    
  usp:
    primary_statement: string
    supporting_points: [string]
    competitive_advantages: [string]
    
  messaging:
    tone: string
    key_messages: [
      {
        segment: string,
        message: string,
        channels: [string]
      }
    ]
```

# Level 3: Content Strategy

```yaml
content_strategy:
  manifesto:
    purpose: string
    beliefs: [string]
    stance: string
    
  narrative:
    story_arc: [string]
    key_themes: [string]
    success_stories: [
      {
        title: string,
        challenge: string,
        solution: string,
        outcome: string
      }
    ]
    
  content_pillars: [
    {
      name: string,
      topics: [string],
      expertise_level: string,
      content_ratio: number
    }
  ]
    
  point_of_view:
    industry_stance: string
    thought_leadership: [string]
    innovation_areas: [string]
    
  enemy:
    problems: [string]
    pain_points: [string]
    alternatives: [string]
```

# Level 4: Content Plan

```yaml
content_plan:
  channels: [
    {
      name: string,
      purpose: string,
      metrics: [string],
      frequency: string
    }
  ]
    
  formats: [
    {
      type: string,
      requirements: [string],
      resources: [string]
    }
  ]
    
  distribution:
    primary_channels: [string]
    promotion_tactics: [string]
    schedule:
      frequency: string
      best_times: [string]
      
  repurposing:
    content_maps: [
      {
        source_format: string,
        target_formats: [string],
        modifications: [string]
      }
    ]
    
  timeline:
    milestones: [
      {
        date: date,
        deliverable: string,
        owner: string
      }
    ]
```

# Level 5: Content Execution

```yaml
content:
  copywriting:
    guidelines:
      style: string
      tone: string
      word_count: number
      seo_requirements: [string]
    
  design:
    brand_colors: [string]
    typography:
      primary_font: string
      secondary_font: string
    image_specs:
      formats: [string]
      sizes: [string]
    
  videos:
    types: [
      {
        format: string,
        duration: string,
        specifications: [string]
      }
    ]
    
  pages:
    templates: [
      {
        name: string,
        sections: [string],
        components: [string]
      }
    ]
    
  social:
    platforms: [
      {
        name: string,
        content_types: [string],
        posting_frequency: string,
        engagement_rules: [string]
      }
    ]
```

# Metadata

```yaml
metadata:
  version: string
  last_updated: date
  owner: string
  status: enum[draft, review, approved, archived]
  dependencies: [string]
```
