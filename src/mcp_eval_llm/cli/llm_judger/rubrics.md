# LLM Multi-Aspect Evaluation Rubrics

This document defines the evaluation criteria and scoring rubrics used in the LLM multi-aspect evaluation system for AI agent execution trajectories and task completion.

## Trajectory Evaluation Aspects

### 1. Planning (0.0 - 1.0)
**Definition**: How well did the agent understand and decompose the task?

**Scoring Criteria**:
- **1.0 - Excellent**: Perfect task understanding, clear decomposition into logical steps, identifies all necessary components and dependencies
- **0.8-0.9 - Very Good**: Good task understanding with minor gaps, mostly clear decomposition, identifies most necessary components
- **0.6-0.7 - Good**: Adequate task understanding, basic decomposition present, some important components identified
- **0.4-0.5 - Fair**: Limited task understanding, unclear or incomplete decomposition, misses key components
- **0.0-0.3 - Poor**: Minimal or incorrect task understanding, no clear decomposition, fails to identify necessary components

**Key Indicators**:
- Clear articulation of task requirements
- Logical breakdown of complex tasks into subtasks
- Identification of necessary resources and dependencies
- Appropriate sequencing of planned actions

### 2. Execution Flow (0.0 - 1.0)
**Definition**: Was the sequence of actions logical and well-structured?

**Scoring Criteria**:
- **1.0 - Excellent**: Perfect logical sequence, smooth transitions between steps, optimal ordering of actions
- **0.8-0.9 - Very Good**: Generally logical sequence with minor inefficiencies, good transitions between steps
- **0.6-0.7 - Good**: Mostly logical sequence, some awkward transitions or suboptimal ordering
- **0.4-0.5 - Fair**: Sequence has logical gaps, confusing transitions, some actions out of order
- **0.0-0.3 - Poor**: Illogical sequence, poor transitions, actions significantly out of order

**Key Indicators**:
- Logical progression from one step to the next
- Appropriate sequencing of dependent actions
- Smooth integration of tool results into subsequent steps
- Coherent overall execution narrative

### 3. Tool Selection (0.0 - 1.0)
**Definition**: Were the right tools chosen for each step?

**Scoring Criteria**:
- **1.0 - Excellent**: Perfect tool selection for all steps, optimal choices for each specific need
- **0.8-0.9 - Very Good**: Appropriate tool selection with minor suboptimal choices
- **0.6-0.7 - Good**: Generally appropriate tools, some suboptimal but functional choices
- **0.4-0.5 - Fair**: Mixed tool selection, some inappropriate choices that still work
- **0.0-0.3 - Poor**: Frequent inappropriate tool selection, choices that don't match needs

**Key Indicators**:
- Appropriate tool for each specific task requirement
- Consideration of tool capabilities and limitations
- Efficient tool usage (not using complex tools for simple tasks)
- Awareness of available tool alternatives

### 4. Tool Usage (0.0 - 1.0)
**Definition**: Were tool parameters correct and results properly interpreted?

**Scoring Criteria**:
- **1.0 - Excellent**: Perfect parameter formatting and values, excellent interpretation of all results
- **0.8-0.9 - Very Good**: Correct parameters with minor issues, good interpretation of results
- **0.6-0.7 - Good**: Mostly correct parameters, adequate interpretation with some minor misunderstandings
- **0.4-0.5 - Fair**: Some parameter errors, limited interpretation of results
- **0.0-0.3 - Poor**: Frequent parameter errors, poor or incorrect interpretation of results

**Key Indicators**:
- Correct parameter syntax and data types
- Appropriate parameter values for the context
- Accurate interpretation of tool responses
- Effective integration of tool results into decision-making

### 5. Adaptability (0.0 - 1.0)
**Definition**: How well did the agent handle errors, unexpected results, changing contexts, and alternative paths?

**Scoring Criteria**:
- **1.0 - Excellent**: Perfect handling of all errors/changes OR smooth execution with no issues (indicating robustness)
- **0.8-0.9 - Very Good**: Excellent handling of most errors/changes, minor issues resolved effectively
- **0.6-0.7 - Good**: Adequate handling of some errors/changes, some issues resolved with moderate effectiveness
- **0.4-0.5 - Fair**: Limited handling of errors/changes, some issues left unresolved or poorly addressed
- **0.0-0.3 - Poor**: Poor handling of errors/changes, most issues left unresolved or handled incorrectly

**Key Indicators**:
- Appropriate error recovery strategies
- Flexibility in approach when initial plans don't work
- Ability to pivot based on new information
- Graceful handling of unexpected tool responses
- Maintenance of progress despite obstacles

**Note**: If execution was smooth with no errors or unexpected situations, this indicates good robustness and should receive a high score (0.9-1.0).

### 6. Efficiency (0.0 - 1.0)
**Definition**: Did the agent use an optimal approach without unnecessary steps?

**Scoring Criteria**:
- **1.0 - Excellent**: Optimal approach with minimal steps, no redundancy, maximum efficiency
- **0.8-0.9 - Very Good**: Near-optimal approach with minor inefficiencies, minimal redundancy
- **0.6-0.7 - Good**: Generally efficient approach with some unnecessary steps or redundancy
- **0.4-0.5 - Fair**: Moderately efficient with noticeable unnecessary steps or redundant actions
- **0.0-0.3 - Poor**: Inefficient approach with many unnecessary steps, significant redundancy

**Key Indicators**:
- Minimal number of steps to achieve the goal
- Avoidance of redundant tool calls
- Efficient use of available information
- Optimal resource utilization

### 7. Context Awareness (0.0 - 1.0)
**Definition**: Did the agent maintain awareness of relevant context, constraints, and environmental state throughout execution?

**Scoring Criteria**:
- **1.0 - Excellent**: Perfect awareness of all relevant context, constraints, and state changes
- **0.8-0.9 - Very Good**: Good awareness with minor gaps, mostly maintains relevant context
- **0.6-0.7 - Good**: Adequate awareness, some context maintained but occasional gaps
- **0.4-0.5 - Fair**: Limited awareness, frequently loses important context or ignores constraints
- **0.0-0.3 - Poor**: Poor awareness, consistently ignores context, constraints, or state changes

**Key Indicators**:
- Awareness of task constraints and requirements
- Tracking of environmental state changes
- Consideration of previous actions and their outcomes
- Maintenance of relevant context across multiple steps

## Task Completion Evaluation Aspects

### 1. Requirement Coverage (0.0 - 1.0)
**Definition**: Did the agent address all aspects of the task?

**Scoring Criteria**:
- **1.0 - Excellent**: All task requirements fully addressed, no aspects missed
- **0.8-0.9 - Very Good**: Most requirements addressed, minor aspects may be incomplete
- **0.6-0.7 - Good**: Major requirements addressed, some minor requirements missed
- **0.4-0.5 - Fair**: Some requirements addressed, several important aspects missed
- **0.0-0.3 - Poor**: Few requirements addressed, most aspects missed or incomplete

**Key Indicators**:
- Completeness against original task specification
- Coverage of all stated deliverables
- Addressing both explicit and implicit requirements
- Fulfillment of success criteria

### 2. Accuracy (0.0 - 1.0)
**Definition**: Is the information and analysis factually correct?

**Scoring Criteria**:
- **1.0 - Excellent**: All information completely accurate, no factual errors
- **0.8-0.9 - Very Good**: Mostly accurate with minor errors that don't affect conclusions
- **0.6-0.7 - Good**: Generally accurate with some errors, conclusions mostly valid
- **0.4-0.5 - Fair**: Mixed accuracy, some significant errors that may affect conclusions
- **0.0-0.3 - Poor**: Frequent inaccuracies, major errors that invalidate conclusions

**Key Indicators**:
- Factual correctness of data and information
- Accuracy of calculations and analysis
- Correctness of interpretations and conclusions
- Validity of recommendations or insights

### 3. Completeness (0.0 - 1.0)
**Definition**: Is the response thorough and comprehensive?

**Scoring Criteria**:
- **1.0 - Excellent**: Fully comprehensive response covering all relevant aspects in appropriate detail
- **0.8-0.9 - Very Good**: Thorough response with minor gaps, good level of detail
- **0.6-0.7 - Good**: Adequate completeness, some areas could be more detailed
- **0.4-0.5 - Fair**: Limited completeness, several areas lacking sufficient detail
- **0.0-0.3 - Poor**: Incomplete response, major gaps in coverage or detail

**Key Indicators**:
- Depth of analysis and explanation
- Coverage of relevant supporting information
- Appropriate level of detail for the context
- Inclusion of necessary context and background

### 4. Usefulness (0.0 - 1.0)
**Definition**: Is the final result practically valuable to the user?

**Scoring Criteria**:
- **1.0 - Excellent**: Extremely valuable and actionable, directly addresses user needs
- **0.8-0.9 - Very Good**: Very useful with clear practical value, mostly addresses user needs
- **0.6-0.7 - Good**: Useful with some practical value, partially addresses user needs
- **0.4-0.5 - Fair**: Limited usefulness, minimal practical value for the user
- **0.0-0.3 - Poor**: Not useful, no clear practical value or relevance to user needs

**Key Indicators**:
- Practical applicability of the results
- Relevance to user's stated or implied needs
- Actionability of recommendations or insights
- Clear value proposition for the user

## Scoring Guidelines

### General Principles
1. **Holistic Assessment**: Consider the overall quality and coherence of the execution
2. **Context Sensitivity**: Adjust expectations based on task complexity and requirements
3. **Consistent Standards**: Apply the same criteria consistently across similar tasks
4. **Evidence-Based**: Base scores on observable evidence in the execution trajectory

### Score Interpretation
- **0.9-1.0**: Exceptional performance, professional-grade execution
- **0.8-0.89**: Very good performance, minor room for improvement
- **0.7-0.79**: Good performance, some notable areas for improvement
- **0.6-0.69**: Adequate performance, several areas needing improvement
- **0.5-0.59**: Below average performance, significant improvement needed
- **0.0-0.49**: Poor performance, major issues requiring attention

### Common Scoring Considerations
- **Task Complexity**: More complex tasks may warrant more lenient scoring for minor issues
- **Error Recovery**: Successful error recovery should be weighted positively
- **Innovation**: Creative or innovative approaches should be recognized
- **Efficiency vs. Thoroughness**: Balance between speed and completeness based on task requirements 