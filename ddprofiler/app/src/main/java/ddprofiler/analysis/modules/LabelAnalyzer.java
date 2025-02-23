package ddprofiler.analysis.modules;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import ddprofiler.analysis.TextualDataConsumer;
import ddprofiler.core.config.ProfilerConfig;
import xsystem.layers.XStructure;
import xsystem.learning.LearningModel;
import xsystem.learning.XStructType;

public class LabelAnalyzer implements TextualDataConsumer {

    final private Logger LOG = LoggerFactory.getLogger(LabelAnalyzer.class.getName());

    private ProfilerConfig pc;
    private double scoreThreshold;
    private static ArrayList<XStructType> xStructureReference = null;
    private String label;
    private static boolean isThisAnalyzerIncluded = false;

    public LabelAnalyzer(ProfilerConfig pc) {
        this.pc = pc;
        this.scoreThreshold = pc.getDouble(ProfilerConfig.XSYSTEM_SIMILARITY_THRESHOLD);

        String excludedAnalyzer = pc.getString(ProfilerConfig.EXCLUDE_ANALYZER);
        if (!excludedAnalyzer.contains("Label")) isThisAnalyzerIncluded = true;

        if (xStructureReference == null && isThisAnalyzerIncluded) {
            String referenceFilePath = pc.getString(ProfilerConfig.XSYSTEM_REFERENCE_FILE);
            xStructureReference = (new LearningModel()).readXStructsfromJSON(referenceFilePath);
        } else {
            LOG.warn("Reference file already initialized or XSystem is not enabled");
        }
    }

    @Override
    public boolean feedTextData(List<String> records) {
        if (records == null || records.isEmpty()) {
            LOG.warn("No records to analyze");
        }
        if (LabelAnalyzer.xStructureReference == null) {
            LOG.warn("Reference file not initialized");
        }
        if (isThisAnalyzerIncluded) {
            label = labelListOfStrings((ArrayList<String>) records);
        } else {
            LOG.info("XSystem is not enabled");
        }
        return true;
    }

    private String labelListOfStrings(ArrayList<String> strings) {
        String label = null;
        ArrayList<Double> scoreList = new ArrayList<>();
        XStructure toBeLabeled = (new XStructure()).addNewLines(strings);

        for (XStructType struct : xStructureReference) {
            double score = struct.xStructure.compareTwo(toBeLabeled, struct.xStructure);
            LOG.debug("Item compared with " + struct.type + " has similarity score " + score);
            scoreList.add(score);
        }
        double maxScore = Collections.max(scoreList);
        int maxIndex = scoreList.indexOf(maxScore);

        if (maxScore >= scoreThreshold) {
            label = xStructureReference.get(maxIndex).type;
            return label;
        }

        return label;
    }

    public static void nullifyXStructureReference() {
        LabelAnalyzer.xStructureReference = null;
    }

    public String getLabel() {
        return label;
    }
    
}
