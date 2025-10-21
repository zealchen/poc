XML_EXAMPLE_MAP = {
    "choice": """
    <?xml version="1.0" encoding="UTF-8"?>
<qti-assessment-item xmlns="http://www.imsglobal.org/xsd/imsqti_v3p0" 
    identifier="choice-sample" title="Sample Question">
    
    <!-- Response declaration defines the response variable -->
    <qti-response-declaration identifier="RESPONSE" cardinality="single" base-type="identifier">
        <qti-correct-response>
            <qti-value>choice-2</qti-value>
        </qti-correct-response>
    </qti-response-declaration>
    
    <!-- Outcome declarations define score variables -->
    <qti-outcome-declaration identifier="SCORE" cardinality="single" base-type="float">
        <qti-default-value>
            <qti-value>0</qti-value>
        </qti-default-value>
    </qti-outcome-declaration>
    
    <qti-outcome-declaration identifier="MAXSCORE" cardinality="single" base-type="float">
        <qti-default-value>
            <qti-value>1</qti-value>
        </qti-default-value>
    </qti-outcome-declaration>
    
    <!-- The question content -->
    <qti-item-body>
        <p>What is the capital of France?</p>
        <qti-choice-interaction response-identifier="RESPONSE">
            <qti-simple-choice identifier="choice-1">London</qti-simple-choice>
            <qti-simple-choice identifier="choice-2">Paris</qti-simple-choice>
            <qti-simple-choice identifier="choice-3">Berlin</qti-simple-choice>
        </qti-choice-interaction>
    </qti-item-body>
    
    <!-- Response processing rules for scoring -->
    <qti-response-processing>
        <qti-response-condition>
            <qti-response-if>
                <qti-match>
                    <qti-variable identifier="RESPONSE"/>
                    <qti-correct/>
                </qti-match>
                <qti-set-outcome-value identifier="SCORE">
                    <qti-base-value base-type="float">1</qti-base-value>
                </qti-set-outcome-value>
            </qti-response-if>
            <qti-response-else>
                <qti-set-outcome-value identifier="SCORE">
                    <qti-base-value base-type="float">0</qti-base-value>
                </qti-set-outcome-value>
            </qti-response-else>
        </qti-response-condition>
    </qti-response-processing>
</qti-assessment-item>
    """,
    "text": """
    <?xml version="1.0" encoding="UTF-8"?>
<qti-assessment-item
    xmlns="http://www.imsglobal.org/xsd/imsqtiasi_v3p0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqtiasi_v3p0 https://purl.imsglobal.org/spec/qti/v3p0/schema/xsd/imsqti_asiv3p0_v1p0.xsd"
    identifier="text-entry-sample"
    title="Text Entry Question"
    adaptive="false"
    time-dependent="false">
    
    <!-- Response Declaration -->
    <qti-response-declaration identifier="RESPONSE" cardinality="single" base-type="string">
        <qti-correct-response>
            <qti-value>Paris</qti-value>
        </qti-correct-response>
    </qti-response-declaration>
    
    <!-- Outcome Declarations -->
    <qti-outcome-declaration identifier="SCORE" cardinality="single" base-type="float">
        <qti-default-value>
            <qti-value>0</qti-value>
        </qti-default-value>
    </qti-outcome-declaration>
    
    <qti-outcome-declaration identifier="MAXSCORE" cardinality="single" base-type="float">
        <qti-default-value>
            <qti-value>1</qti-value>
        </qti-default-value>
    </qti-outcome-declaration>
    
    <qti-outcome-declaration identifier="completionStatus" cardinality="single" base-type="identifier">
        <qti-default-value>
            <qti-value>not_attempted</qti-value>
        </qti-default-value>
    </qti-outcome-declaration>
    
    <!-- Item Body -->
    <qti-item-body>
        <h2>Geography Question</h2>
        <p>What is the capital of France? <qti-text-entry-interaction response-identifier="RESPONSE" expected-length="20" placeholder-text="Enter city name..."/></p>
        
        <p class="instruction">Type your answer in the box above. The answer is case-insensitive.</p>
    </qti-item-body>
    
    <!-- Response Processing -->
    <qti-response-processing>
        <qti-response-condition>
            <qti-response-if>
                <qti-string-match case-sensitive="false">
                    <qti-variable identifier="RESPONSE"/>
                    <qti-correct identifier="RESPONSE"/>
                </qti-string-match>
                <qti-set-outcome-value identifier="SCORE">
                    <qti-base-value base-type="float">1</qti-base-value>
                </qti-set-outcome-value>
                <qti-set-outcome-value identifier="completionStatus">
                    <qti-base-value base-type="identifier">completed</qti-base-value>
                </qti-set-outcome-value>
            </qti-response-if>
            <qti-response-else>
                <qti-set-outcome-value identifier="SCORE">
                    <qti-base-value base-type="float">0</qti-base-value>
                </qti-set-outcome-value>
                <qti-set-outcome-value identifier="completionStatus">
                    <qti-base-value base-type="identifier">completed</qti-base-value>
                </qti-set-outcome-value>
            </qti-response-else>
        </qti-response-condition>
    </qti-response-processing>
    
</qti-assessment-item>
    """,
    "gap_match": """
    <?xml version="1.0" encoding="UTF-8"?>
<qti-assessment-item xmlns="http://www.imsglobal.org/xsd/imsqti_v3p0" 
    identifier="gap-match-sample" 
    title="Gap Match Question">
    
    <!-- Response declaration for gap match (pairs of identifiers) -->
    <qti-response-declaration identifier="RESPONSE" cardinality="multiple" base-type="directedPair">
        <qti-correct-response>
            <qti-value>paris gap1</qti-value>
            <qti-value>berlin gap2</qti-value>
        </qti-correct-response>
    </qti-response-declaration>
    
    <!-- Outcome declarations for scoring -->
    <qti-outcome-declaration identifier="SCORE" cardinality="single" base-type="float">
        <qti-default-value>
            <qti-value>0</qti-value>
        </qti-default-value>
    </qti-outcome-declaration>
    
    <qti-outcome-declaration identifier="MAXSCORE" cardinality="single" base-type="float">
        <qti-default-value>
            <qti-value>2</qti-value>
        </qti-default-value>
    </qti-outcome-declaration>
    
    <!-- The question content -->
    <qti-item-body>
        <qti-gap-match-interaction response-identifier="RESPONSE" shuffle="true">
            <qti-prompt>Drag the city names to complete the sentences about European capitals.</qti-prompt>
            
            <p>The capital of France is <qti-gap identifier="gap1" required="false"/> and the capital of Germany is <qti-gap identifier="gap2" required="false"/>.</p>
            
            <!-- Available gap texts (draggable items) -->
            <qti-gap-text identifier="paris" match-max="1">Paris</qti-gap-text>
            <qti-gap-text identifier="berlin" match-max="1">Berlin</qti-gap-text>
            <qti-gap-text identifier="london" match-max="1">London</qti-gap-text>
            <qti-gap-text identifier="rome" match-max="1">Rome</qti-gap-text>
        </qti-gap-match-interaction>
    </qti-item-body>
    
    <!-- Response processing rules for scoring -->
    <qti-response-processing>
        <qti-response-condition>
            <qti-response-if>
                <qti-match>
                    <qti-variable identifier="RESPONSE"/>
                    <qti-correct/>
                </qti-match>
                <qti-set-outcome-value identifier="SCORE">
                    <qti-base-value base-type="float">2</qti-base-value>
                </qti-set-outcome-value>
            </qti-response-if>
            <qti-response-else>
                <qti-set-outcome-value identifier="SCORE">
                    <qti-base-value base-type="float">0</qti-base-value>
                </qti-set-outcome-value>
            </qti-response-else>
        </qti-response-condition>
    </qti-response-processing>
</qti-assessment-item>
    """
}
