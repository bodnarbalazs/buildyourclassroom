const PAPERS = [
  {
    theme: "Attention & Learning",
    items: [
      {
        citation:
          'Rosegard, E., & Wilson, J. (2013). Capturing students\u2019 attention: An empirical study. \u003Cem\u003EJournal of the Scholarship of Teaching and Learning, 13\u003C/em\u003E(5), 1\u201320.',
        finding:
          "A 90-second external stimulus (hook/attention getter) before a lecture significantly increases information retention (p < .001, n = 846). Arousal from novel, unexpected stimuli triggers curiosity and focused attention, enhancing encoding and memory.",
        relevance: "Classroom Builder",
        connection:
          "Supports inclusion of energizers and attention-getting segments when structuring lesson plans into timed pedagogical blocks.",
      },
      {
        citation:
          'Bunce, D. M., Flens, E. A., & Neiles, K. Y. (2010). How long can students pay attention in class? A study of student attention decline using clickers. \u003Cem\u003EJournal of Chemical Education, 87\u003C/em\u003E(12), 1438\u20131443.',
        finding:
          "Student attention does not decline in a single drop after 10\u201320 minutes. Instead, lapses occur in short cycles every 3\u20134 minutes, with attention alternating between engaged and disengaged states throughout a lecture.",
        relevance: "Classroom Builder",
        connection:
          "Validates the approach of breaking lessons into short, varied segments rather than long uninterrupted lecture blocks.",
      },
      {
        citation:
          'Hlas, A. C., Neyers, K., & Molitor, S. (2019). Measuring student attention in the second language classroom. \u003Cem\u003ELanguage Teaching Research, 23\u003C/em\u003E(1), 107\u2013125.',
        finding:
          "Students report short attention lapses (1 min or less), 2\u20133 times per class. Active learning moments (e.g., calling on students randomly) increase attention; passive moments (e.g., listening to peers speak) decrease it. Correcting homework consistently leads to more lapses.",
        relevance: "Classroom Builder",
        connection:
          "Supports favouring active over passive learning formats and informs the simulation of student emotional states during different activity types.",
      },
    ],
  },
  {
    theme: "Engagement & Emotion",
    items: [
      {
        citation:
          'Chen, G., Han, G., Niu, J., & He, J. (2026). Understanding the impact of emotional engagement on learning outcomes in online education: An automated analysis approach. \u003Cem\u003EScientific Reports\u003C/em\u003E.',
        finding:
          "Emotional engagement detected via facial expressions (Vision Transformer, 93.8% accuracy) shows a significant positive correlation with learning outcomes. Engagement typically declines after six minutes of learning, with a modest rebound near session end.",
        relevance: "Class Evaluation",
        connection:
          "Directly validates the use of facial emotion detection (DeepFace) to track engagement and demonstrates that facial expression analysis is a reliable proxy for learning effectiveness.",
      },
      {
        citation:
          'Darnell, D. K., & Grieg, P. A. (2019). Student engagement, assessed using heart rate, shows no reset following active learning sessions in lectures. \u003Cem\u003EPLOS ONE, 14\u003C/em\u003E(12), e0225883.',
        finding:
          "Heart rate, as a physiological engagement proxy, shows a steady decline from the beginning to the end of a lecture across 75 classes. Active learning sessions cause a significant spike in heart rate, but it returns to the baseline immediately after. The value of active learning resides in the activity itself.",
        relevance: "Classroom Builder & Class Evaluation",
        connection:
          "Supports designing lessons with regular active learning segments and confirms that physiological engagement measures correlate with behavioural indicators.",
      },
      {
        citation:
          'Wammes, J. D., Ralph, B. C. W., Mills, C., Bosch, N., Duncan, T. L., & Smilek, D. (2019). Disengagement during lectures: Media multitasking and mind wandering in university classrooms. \u003Cem\u003EComputers & Education, 132\u003C/em\u003E, 76\u201389.',
        finding:
          "Media multitasking rates are relatively high and increase as a lecture progresses, while mind wandering rates remain stable. Crucially, media multitasking \u2014 not mind wandering \u2014 is associated with negative learning outcomes.",
        relevance: "Class Evaluation",
        connection:
          "Highlights the importance of tracking external behavioural distractions alongside internal emotional states when evaluating classroom engagement.",
      },
    ],
  },
  {
    theme: "Teaching Interaction",
    items: [
      {
        citation:
          'Zeinstra, L., Kupers, E., Loopers, J., & de Boer, A. (2022). Real-time teacher\u2013student interactions: The dynamic interplay between need supportive teaching and student engagement over the course of one school year. \u003Cem\u003ETeaching and Teacher Education, 120\u003C/em\u003E, 103883.',
        finding:
          "What a teacher does in moment-to-moment interactions \u2014 supporting autonomy, competence, and relatedness \u2014 matters immediately for student engagement. Specific structural patterns in teacher\u2013student interactions were identified both within lessons and across time.",
        relevance: "Classroom Builder",
        connection:
          "Supports the simulation of student emotional states and underscores the importance of varied, need-supportive teaching strategies within a lesson plan.",
      },
    ],
  },
] as const;

const TOOL_COLORS: Record<string, string> = {
  "Classroom Builder": "bg-blue-100 text-blue-800",
  "Class Evaluation": "bg-green-100 text-green-800",
  "Classroom Builder & Class Evaluation": "bg-amber-100 text-amber-800",
};

export default function Research() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-16 flex flex-col gap-12">
      <div className="text-center max-w-3xl mx-auto flex flex-col gap-4">
        <h1 className="text-4xl font-bold text-gray-900">
          Scientific Foundation
        </h1>
        <p className="text-lg text-gray-600">
          Our platform is grounded in peer-reviewed research on student
          attention, emotional engagement, and classroom dynamics. Below are the
          key studies that inform the design of our three tools: Classroom
          Builder, Test Generator, and Class Evaluation.
        </p>
      </div>

      {PAPERS.map((group) => (
        <section key={group.theme} className="flex flex-col gap-6">
          <h2 className="text-2xl font-semibold text-gray-900 border-b border-gray-200 pb-2">
            {group.theme}
          </h2>

          {group.items.map((paper) => (
            <div
              key={paper.citation}
              className="rounded-xl border border-gray-200 bg-white p-6 flex flex-col gap-4"
            >
              <p
                className="text-sm text-gray-700"
                dangerouslySetInnerHTML={{ __html: paper.citation }}
              />

              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">
                  Key Finding
                </h3>
                <p className="text-sm text-gray-800">{paper.finding}</p>
              </div>

              <div>
                <span
                  className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full mb-1 ${TOOL_COLORS[paper.relevance]}`}
                >
                  {paper.relevance}
                </span>
                <p className="text-sm text-gray-600">{paper.connection}</p>
              </div>
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}
