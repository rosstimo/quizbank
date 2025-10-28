# Comprehensive QTI 1.2 XML Schema Reference for Canvas LMS Import

This document provides a complete reference for creating QTI 1.2 XML files that are compatible with Canvas Learning Management System. The schema is based on the IMS QTI 1.2 specification and includes all supported question types and parameters.

## Root Structure

All QTI 1.2 XML files must start with the following structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE questestinterop SYSTEM "ims_qtiasiv1p2.dtd">
<questestinterop 
  xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/ims_qtiasiv1p2 ims_qtiasiv1p2.xsd">
  
  <!-- Assessment content goes here -->
  
</questestinterop>
```

## Core Data Structures

### 1. Assessment Structure

The Assessment is the top-level container for tests/quizzes:

```xml
<assessment title="My Quiz" ident="assessment_001">
  <qticomment>Optional comment about the assessment</qticomment>
  <duration>PT30M</duration> <!-- 30 minutes duration -->
  <qtimetadata>
    <qtimetadatafield>
      <fieldlabel>qmd_assessmenttype</fieldlabel>
      <fieldentry>Examination</fieldentry>
    </qtimetadatafield>
  </qtimetadata>
  
  <assessmentcontrol 
    solutionswitch="Yes" 
    hintswitch="Yes" 
    feedbackswitch="Yes" />
  
  <section ident="section_001">
    <!-- Section content -->
  </section>
</assessment>
```

#### Assessment Attributes:
- `title` (optional): The title of the assessment
- `ident` (required): Unique identifier for the assessment (max 256 chars)
- `xml:lang` (optional): Default language (e.g., "en-US")

#### Assessment Elements:
- `qticomment`: Comments about the assessment
- `duration`: Time limit in ISO 8601 format (PT30M = 30 minutes)
- `qtimetadata`: Metadata about the assessment
- `objectives`: Learning objectives
- `rubric`: Contextual information
- `assessmentcontrol`: Control switches for hints, solutions, feedback
- `presentation_material`: Common presentation material
- `outcomes_processing`: Scoring instructions
- `assessfeedback`: Assessment-level feedback
- `selection_ordering`: Selection and ordering rules
- `section`: One or more sections containing items

### 2. Section Structure

Sections group items for organizational purposes:

```xml
<section title="Section 1" ident="section_001">
  <qticomment>Optional section comment</qticomment>
  <duration>PT15M</duration> <!-- 15 minutes for this section -->
  <qtimetadata>
    <qtimetadatafield>
      <fieldlabel>section_type</fieldlabel>
      <fieldentry>quiz_section</fieldentry>
    </qtimetadatafield>
  </qtimetadata>
  
  <sectioncontrol 
    solutionswitch="Yes" 
    hintswitch="Yes" 
    feedbackswitch="Yes" />
  
  <!-- Items go here -->
  <item ident="item_001">
    <!-- Item content -->
  </item>
</section>
```

#### Section Attributes:
- `title` (optional): Section title
- `ident` (required): Unique identifier
- `xml:lang` (optional): Default language

#### Section Elements:
- `qticomment`: Section comments
- `duration`: Time limit for section
- `qtimetadata`: Section metadata
- `objectives`: Section objectives
- `rubric`: Section rubric
- `sectioncontrol`: Control switches
- `presentation_material`: Common presentation material
- `outcomes_processing`: Section-level processing
- `sectionfeedback`: Section feedback
- `selection_ordering`: Item selection/ordering rules
- `item`: Individual question items

### 3. Item Structure

Items are individual questions:

```xml
<item title="Question 1" ident="item_001" maxattempts="1">
  <qticomment>Optional item comment</qticomment>
  <duration>PT5M</duration> <!-- 5 minutes for this item -->
  
  <itemmetadata>
    <qtimetadata>
      <qtimetadatafield>
        <fieldlabel>qmd_itemtype</fieldlabel>
        <fieldentry>Multiple Choice</fieldentry>
      </qtimetadatafield>
      <qtimetadatafield>
        <fieldlabel>qmd_maximumscore</fieldlabel>
        <fieldentry>1</fieldentry>
      </qtimetadatafield>
    </qtimetadata>
  </itemmetadata>
  
  <itemcontrol 
    solutionswitch="Yes" 
    hintswitch="Yes" 
    feedbackswitch="Yes" />
  
  <presentation>
    <!-- Question presentation -->
  </presentation>
  
  <resprocessing>
    <!-- Response processing -->
  </resprocessing>
  
  <itemfeedback ident="correct_fb">
    <!-- Feedback -->
  </itemfeedback>
</item>
```

#### Item Attributes:
- `title` (optional): Question title
- `ident` (required): Unique identifier
- `maxattempts` (optional): Maximum attempts allowed
- `label` (optional): Authoring label
- `xml:lang` (optional): Default language

## Question Types and Presentation

### 1. Multiple Choice Questions

```xml
<presentation>
  <material>
    <mattext>What is the capital of France?</mattext>
  </material>
  
  <response_lid ident="response_001" rcardinality="Single" rtiming="No">
    <render_choice shuffle="Yes" minnumber="1" maxnumber="1">
      <response_label ident="A">
        <material>
          <mattext>London</mattext>
        </material>
      </response_label>
      <response_label ident="B">
        <material>
          <mattext>Berlin</mattext>
        </material>
      </response_label>
      <response_label ident="C">
        <material>
          <mattext>Paris</mattext>
        </material>
      </response_label>
      <response_label ident="D">
        <material>
          <mattext>Madrid</mattext>
        </material>
      </response_label>
    </render_choice>
  </response_lid>
</presentation>
```

### 2. Multiple Response Questions

```xml
<presentation>
  <material>
    <mattext>Which of the following are programming languages? (Select all that apply)</mattext>
  </material>
  
  <response_lid ident="response_001" rcardinality="Multiple" rtiming="No">
    <render_choice shuffle="Yes">
      <response_label ident="A">
        <material>
          <mattext>Java</mattext>
        </material>
      </response_label>
      <response_label ident="B">
        <material>
          <mattext>HTML</mattext>
        </material>
      </response_label>
      <response_label ident="C">
        <material>
          <mattext>Python</mattext>
        </material>
      </response_label>
      <response_label ident="D">
        <material>
          <mattext>C++</mattext>
        </material>
      </response_label>
    </render_choice>
  </response_lid>
</presentation>
```

### 3. True/False Questions

```xml
<presentation>
  <material>
    <mattext>Paris is the capital of France.</mattext>
  </material>
  
  <response_lid ident="response_001" rcardinality="Single" rtiming="No">
    <render_choice>
      <response_label ident="T">
        <material>
          <mattext>True</mattext>
        </material>
      </response_label>
      <response_label ident="F">
        <material>
          <mattext>False</mattext>
        </material>
      </response_label>
    </render_choice>
  </response_lid>
</presentation>
```

### 4. Fill-in-the-Blank (String Response)

```xml
<presentation>
  <material>
    <mattext>The capital of France is ________.</mattext>
  </material>
  
  <response_str ident="response_001" rcardinality="Single" rtiming="No">
    <render_fib charset="ascii-us" encoding="UTF_8" 
               rows="1" columns="20" maxchars="50" />
  </response_str>
</presentation>
```

### 5. Numerical Response

```xml
<presentation>
  <material>
    <mattext>What is 2 + 2?</mattext>
  </material>
  
  <response_num ident="response_001" rcardinality="Single" rtiming="No">
    <render_fib charset="ascii-us" encoding="UTF_8" 
               rows="1" columns="10" maxchars="10" />
  </response_num>
</presentation>
```

### 6. Essay Questions

```xml
<presentation>
  <material>
    <mattext>Describe the process of photosynthesis in plants.</mattext>
  </material>
  
  <response_str ident="response_001" rcardinality="Single" rtiming="No">
    <render_fib charset="ascii-us" encoding="UTF_8" 
               rows="10" columns="80" maxchars="5000" />
  </response_str>
</presentation>
```

### 7. Hotspot/Image Questions

```xml
<presentation>
  <material>
    <mattext>Click on Paris in the map below:</mattext>
    <matimage uri="europe_map.jpg" />
  </material>
  
  <response_xy ident="response_001" rcardinality="Single" rtiming="No">
    <render_hotspot>
      <response_label ident="paris">
        <material>
          <mattext>Paris</mattext>
        </material>
        <flow_label class="hotspot">100,150,20,20</flow_label>
      </response_label>
    </render_hotspot>
  </response_xy>
</presentation>
```

## Response Processing

Response processing defines how answers are evaluated and scored:

### Basic Response Processing Template

```xml
<resprocessing>
  <outcomes>
    <decvar varname="SCORE" vartype="Decimal" defaultval="0" minvalue="0" maxvalue="1" />
  </outcomes>
  
  <respcondition continue="No" title="correct">
    <conditionvar>
      <varequal respident="response_001">C</varequal>
    </conditionvar>
    <setvar action="Set" varname="SCORE">1</setvar>
    <displayfeedback feedbacktype="Response" linkrefid="correct_fb" />
  </respcondition>
  
  <respcondition continue="Yes" title="incorrect">
    <conditionvar>
      <other />
    </conditionvar>
    <setvar action="Set" varname="SCORE">0</setvar>
    <displayfeedback feedbacktype="Response" linkrefid="incorrect_fb" />
  </respcondition>
</resprocessing>
```

### Multiple Response Processing

```xml
<resprocessing>
  <outcomes>
    <decvar varname="SCORE" vartype="Decimal" defaultval="0" minvalue="0" maxvalue="1" />
  </outcomes>
  
  <respcondition continue="No" title="correct">
    <conditionvar>
      <and>
        <varequal respident="response_001">A</varequal>
        <varequal respident="response_001">C</varequal>
        <varequal respident="response_001">D</varequal>
      </and>
    </conditionvar>
    <setvar action="Set" varname="SCORE">1</setvar>
    <displayfeedback feedbacktype="Response" linkrefid="correct_fb" />
  </respcondition>
  
  <respcondition continue="Yes" title="partial">
    <conditionvar>
      <or>
        <varequal respident="response_001">A</varequal>
        <varequal respident="response_001">C</varequal>
        <varequal respident="response_001">D</varequal>
      </or>
    </conditionvar>
    <setvar action="Add" varname="SCORE">0.33</setvar>
    <displayfeedback feedbacktype="Response" linkrefid="partial_fb" />
  </respcondition>
</resprocessing>
```

### String Response Processing

```xml
<resprocessing>
  <outcomes>
    <decvar varname="SCORE" vartype="Decimal" defaultval="0" minvalue="0" maxvalue="1" />
  </outcomes>
  
  <respcondition continue="No" title="correct">
    <conditionvar>
      <or>
        <varequal respident="response_001" case="No">Paris</varequal>
        <varequal respident="response_001" case="No">paris</varequal>
      </or>
    </conditionvar>
    <setvar action="Set" varname="SCORE">1</setvar>
    <displayfeedback feedbacktype="Response" linkrefid="correct_fb" />
  </respcondition>
</resprocessing>
```

### Numerical Response Processing

```xml
<resprocessing>
  <outcomes>
    <decvar varname="SCORE" vartype="Decimal" defaultval="0" minvalue="0" maxvalue="1" />
  </outcomes>
  
  <respcondition continue="No" title="correct">
    <conditionvar>
      <varequal respident="response_001">4</varequal>
    </conditionvar>
    <setvar action="Set" varname="SCORE">1</setvar>
    <displayfeedback feedbacktype="Response" linkrefid="correct_fb" />
  </respcondition>
  
  <!-- Range-based scoring -->
  <respcondition continue="No" title="close">
    <conditionvar>
      <and>
        <vargte respident="response_001">3.8</vargte>
        <varlte respident="response_001">4.2</varlte>
      </and>
    </conditionvar>
    <setvar action="Set" varname="SCORE">0.8</setvar>
    <displayfeedback feedbacktype="Response" linkrefid="close_fb" />
  </respcondition>
</resprocessing>
```

## Feedback

### Item-Level Feedback

```xml
<itemfeedback ident="correct_fb" view="All">
  <material>
    <mattext>Correct! Paris is indeed the capital of France.</mattext>
  </material>
</itemfeedback>

<itemfeedback ident="incorrect_fb" view="All">
  <material>
    <mattext>Incorrect. The capital of France is Paris.</mattext>
  </material>
</itemfeedback>

<itemfeedback ident="partial_fb" view="All">
  <material>
    <mattext>Partially correct. You selected some right answers.</mattext>
  </material>
</itemfeedback>
```

### Response-Specific Feedback

```xml
<itemfeedback ident="choice_A_fb" view="All">
  <material>
    <mattext>London is the capital of the United Kingdom, not France.</mattext>
  </material>
</itemfeedback>

<itemfeedback ident="choice_B_fb" view="All">
  <material>
    <mattext>Berlin is the capital of Germany, not France.</mattext>
  </material>
</itemfeedback>
```

## Material Types

### Text Material

```xml
<material>
  <mattext charset="ascii-us" texttype="text/plain">
    This is plain text content.
  </mattext>
</material>
```

### HTML Material

```xml
<material>
  <mattext charset="ascii-us" texttype="text/html">
    <![CDATA[
    <p>This is <strong>HTML</strong> content with <em>formatting</em>.</p>
    <ul>
      <li>Item 1</li>
      <li>Item 2</li>
    </ul>
    ]]>
  </mattext>
</material>
```

### Image Material

```xml
<material>
  <matimage uri="images/diagram.png" 
            imagtype="image/png" 
            label="Diagram" 
            height="200" 
            width="300" />
</material>
```

### Audio Material

```xml
<material>
  <mataudio uri="audio/pronunciation.mp3" 
            audiotype="audio/mpeg" 
            label="Pronunciation" />
</material>
```

### Video Material

```xml
<material>
  <matvideo uri="videos/explanation.mp4" 
            videotype="video/mp4" 
            label="Explanation Video" 
            height="480" 
            width="640" />
</material>
```

## Metadata

### Assessment Metadata

```xml
<qtimetadata>
  <qtimetadatafield>
    <fieldlabel>qmd_assessmenttype</fieldlabel>
    <fieldentry>Examination</fieldentry>
  </qtimetadatafield>
  <qtimetadatafield>
    <fieldlabel>qmd_timelimit</fieldlabel>
    <fieldentry>3600</fieldentry> <!-- seconds -->
  </qtimetadatafield>
  <qtimetadatafield>
    <fieldlabel>qmd_maximumscore</fieldlabel>
    <fieldentry>100</fieldentry>
  </qtimetadatafield>
</qtimetadata>
```

### Item Metadata

```xml
<qtimetadata>
  <qtimetadatafield>
    <fieldlabel>qmd_itemtype</fieldlabel>
    <fieldentry>Multiple Choice</fieldentry>
  </qtimetadatafield>
  <qtimetadatafield>
    <fieldlabel>qmd_maximumscore</fieldlabel>
    <fieldentry>1</fieldentry>
  </qtimetadatafield>
  <qtimetadatafield>
    <fieldlabel>qmd_levelofdifficulty</fieldlabel>
    <fieldentry>Medium</fieldentry>
  </qtimetadatafield>
  <qtimetadatafield>
    <fieldlabel>qmd_topic</fieldlabel>
    <fieldentry>Geography</fieldentry>
  </qtimetadatafield>
</qtimetadata>
```

## Canvas-Specific Considerations

1. **Question Types Supported by Canvas:**
   - Multiple Choice (single answer)
   - Multiple Response (multiple answers)
   - True/False
   - Fill-in-the-Blank
   - Short Answer/Essay
   - Numerical Answer
   - Matching
   - Ordering

2. **Canvas Import Requirements:**
   - Files must be in a ZIP package
   - Include imsmanifest.xml file for packaging
   - Use UTF-8 encoding
   - Maximum file size limits apply

3. **Canvas-Specific Features:**
   - Points per question (use qmd_maximumscore)
   - Question groups (use sections)
   - Randomization (use shuffle attributes)
   - Feedback display options

## Complete Example: Multi-Question Quiz

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE questestinterop SYSTEM "ims_qtiasiv1p2.dtd">
<questestinterop>
  <assessment title="Sample Quiz" ident="quiz_001">
    <assessmentcontrol solutionswitch="Yes" feedbackswitch="Yes" />
    
    <section title="General Knowledge" ident="section_001">
      
      <!-- Multiple Choice Question -->
      <item title="Geography Question" ident="item_001">
        <itemmetadata>
          <qtimetadata>
            <qtimetadatafield>
              <fieldlabel>qmd_itemtype</fieldlabel>
              <fieldentry>Multiple Choice</fieldentry>
            </qtimetadatafield>
            <qtimetadatafield>
              <fieldlabel>qmd_maximumscore</fieldlabel>
              <fieldentry>2</fieldentry>
            </qtimetadatafield>
          </qtimetadata>
        </itemmetadata>
        
        <presentation>
          <material>
            <mattext>What is the capital of France?</mattext>
          </material>
          <response_lid ident="response_001" rcardinality="Single">
            <render_choice shuffle="Yes">
              <response_label ident="A">
                <material><mattext>London</mattext></material>
              </response_label>
              <response_label ident="B">
                <material><mattext>Berlin</mattext></material>
              </response_label>
              <response_label ident="C">
                <material><mattext>Paris</mattext></material>
              </response_label>
              <response_label ident="D">
                <material><mattext>Madrid</mattext></material>
              </response_label>
            </render_choice>
          </response_lid>
        </presentation>
        
        <resprocessing>
          <outcomes>
            <decvar varname="SCORE" vartype="Decimal" defaultval="0" minvalue="0" maxvalue="2" />
          </outcomes>
          <respcondition continue="No">
            <conditionvar>
              <varequal respident="response_001">C</varequal>
            </conditionvar>
            <setvar action="Set" varname="SCORE">2</setvar>
            <displayfeedback feedbacktype="Response" linkrefid="correct_fb" />
          </respcondition>
          <respcondition continue="Yes">
            <conditionvar><other /></conditionvar>
            <setvar action="Set" varname="SCORE">0</setvar>
            <displayfeedback feedbacktype="Response" linkrefid="incorrect_fb" />
          </respcondition>
        </resprocessing>
        
        <itemfeedback ident="correct_fb">
          <material><mattext>Correct! Paris is the capital of France.</mattext></material>
        </itemfeedback>
        <itemfeedback ident="incorrect_fb">
          <material><mattext>Incorrect. The correct answer is Paris.</mattext></material>
        </itemfeedback>
      </item>
      
      <!-- True/False Question -->
      <item title="Science Question" ident="item_002">
        <itemmetadata>
          <qtimetadata>
            <qtimetadatafield>
              <fieldlabel>qmd_itemtype</fieldlabel>
              <fieldentry>True False</fieldentry>
            </qtimetadatafield>
            <qtimetadatafield>
              <fieldlabel>qmd_maximumscore</fieldlabel>
              <fieldentry>1</fieldentry>
            </qtimetadatafield>
          </qtimetadata>
        </itemmetadata>
        
        <presentation>
          <material>
            <mattext>Water boils at 100 degrees Celsius at sea level.</mattext>
          </material>
          <response_lid ident="response_002" rcardinality="Single">
            <render_choice>
              <response_label ident="True">
                <material><mattext>True</mattext></material>
              </response_label>
              <response_label ident="False">
                <material><mattext>False</mattext></material>
              </response_label>
            </render_choice>
          </response_lid>
        </presentation>
        
        <resprocessing>
          <outcomes>
            <decvar varname="SCORE" vartype="Decimal" defaultval="0" minvalue="0" maxvalue="1" />
          </outcomes>
          <respcondition continue="No">
            <conditionvar>
              <varequal respident="response_002">True</varequal>
            </conditionvar>
            <setvar action="Set" varname="SCORE">1</setvar>
            <displayfeedback feedbacktype="Response" linkrefid="tf_correct_fb" />
          </respcondition>
          <respcondition continue="Yes">
            <conditionvar><other /></conditionvar>
            <setvar action="Set" varname="SCORE">0</setvar>
            <displayfeedback feedbacktype="Response" linkrefid="tf_incorrect_fb" />
          </respcondition>
        </resprocessing>
        
        <itemfeedback ident="tf_correct_fb">
          <material><mattext>Correct! Water boils at 100°C at sea level.</mattext></material>
        </itemfeedback>
        <itemfeedback ident="tf_incorrect_fb">
          <material><mattext>Incorrect. Water does boil at 100°C at sea level.</mattext></material>
        </itemfeedback>
      </item>
      
    </section>
  </assessment>
</questestinterop>
```

## Validation and Testing

1. **XML Validation:**
   - Validate against QTI 1.2 DTD/XSD
   - Check all required attributes
   - Verify proper nesting structure

2. **Canvas Testing:**
   - Import into Canvas test course
   - Verify question display
   - Test response processing
   - Check feedback functionality

3. **Common Issues:**
   - Invalid identifiers (use alphanumeric + underscore)
   - Missing required elements
   - Incorrect attribute values
   - Encoding problems with special characters

This comprehensive schema reference provides all the necessary elements and structures for creating QTI 1.2 XML files that are fully compatible with Canvas LMS import functionality.