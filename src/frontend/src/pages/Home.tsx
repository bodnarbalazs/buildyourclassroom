import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-16 flex flex-col gap-8">
      <h1 className="text-4xl font-bold text-gray-900 mb-4 text-center">
        We help Teach Teachers Teach
      </h1>
      <p className="text-lg text-gray-600 text-center mb-10 max-w-2xl mx-auto">
        Teaching tools that help you simulate, evaluate, and generate tests for your classroom.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div className="rounded-xl border border-gray-200 bg-white p-6 flex flex-col gap-4">
          <div className="w-10 h-10 rounded-lg bg-blue-100" />
          <h2 className="text-lg font-semibold text-gray-900">Classroom Builder</h2>
          <p className="text-sm text-gray-600 mt-2">
            Simulate classroom dynamics before you teach. Test different seating arrangements, lesson plans, and interventions in a safe virtual environment.
          </p>
          <Link to="/classroom-builder" className="inline-block px-5 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors text-sm font-medium mt-auto">
            Open Simulator
          </Link>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 flex flex-col gap-4">
          <div className="w-10 h-10 rounded-lg bg-blue-100" />
          <h2 className="text-lg font-semibold text-gray-900">Test Generator</h2>
          <p className="text-sm text-gray-600 mt-2">
            Upload recordings of your lessons and automatically generate tests from the transcriptions. Perfect for exams, quizzes, and practice tests.
          </p>
          <Link to="/test-generator" className="inline-block px-5 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors text-sm font-medium mt-auto">
            Generate Tests
          </Link>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 flex flex-col gap-4">
          <div className="w-10 h-10 rounded-lg bg-green-100" />
          <h2 className="text-lg font-semibold text-gray-900">Class Evaluation</h2>
          <p className="text-sm text-gray-600 mt-2">
            Use your classroom camera to capture real-time attention and engagement data. Get objective insights into teaching effectiveness and student behavior.
          </p>
          <Link to="/class-evaluation" className="inline-block px-5 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors text-sm font-medium mt-auto">
            Start Evaluation
          </Link>
        </div>
      </div>
    </div>
  );
}
