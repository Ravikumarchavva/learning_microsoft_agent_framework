import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI Agent Chat
          </h1>
          <p className="text-lg text-gray-600 mb-2">
            Powered by AG UI Protocol
          </p>
          <p className="text-sm text-gray-500 mb-8">
            Real-time WebSocket communication with streaming responses
          </p>

          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              <FeatureCard
                icon="🚀"
                title="Real-time Streaming"
                description="See responses as they're generated"
              />
              <FeatureCard
                icon="🔧"
                title="Tool Calling"
                description="Watch agents use tools in real-time"
              />
              <FeatureCard
                icon="🔄"
                title="Auto-reconnect"
                description="Automatic reconnection on disconnect"
              />
              <FeatureCard
                icon="📊"
                title="AG UI Protocol"
                description="Industry-standard event protocol"
              />
            </div>

            <Link
              href="/chat"
              className="inline-block px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
            >
              Start Chat
            </Link>

            <div className="mt-8 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">
                <strong>Setup:</strong>
              </p>
              <ol className="text-sm text-gray-600 text-left list-decimal list-inside space-y-1">
                <li>Start the FastAPI backend: <code className="bg-gray-200 px-1 rounded">uvicorn app:app --reload</code></li>
                <li>Backend should be running on <code className="bg-gray-200 px-1 rounded">http://localhost:8000</code></li>
                <li>Click &quot;Start Chat&quot; to begin!</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
      <div className="text-3xl mb-2">{icon}</div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}
