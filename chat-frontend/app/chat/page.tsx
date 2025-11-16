'use client';

import { useState, useRef, useEffect } from 'react';
import { useAgentWebSocket } from '@/hooks/useAgentWebSocket';
import { Message } from '@/lib/ag-ui-protocol';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ChatPage() {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { messages, isConnected, isProcessing, connectionError, sendMessage } = useAgentWebSocket(
    'ws://localhost:8000/ws/chat'
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !isConnected || isProcessing) return;

    sendMessage(inputValue);
    setInputValue('');
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Agent Chat</h1>
            <p className="text-sm text-gray-500">Powered by AG UI Protocol</p>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : connectionError || 'Disconnected'}
            </span>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Connection Error Banner */}
          {!isConnected && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">
                    <strong>Not connected to backend.</strong> Make sure the FastAPI server is running:
                  </p>
                  <p className="text-xs text-yellow-600 mt-1 font-mono">
                    uvicorn app:app --reload
                  </p>
                </div>
              </div>
            </div>
          )}

          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-12">
              <p className="text-lg">No messages yet. Start a conversation!</p>
            </div>
          )}
          
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {isProcessing && (
            <div className="flex items-center gap-2 text-gray-500">
              <div className="animate-pulse flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animation-delay-200"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animation-delay-400"></div>
              </div>
              <span className="text-sm">Agent is thinking...</span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-4">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your message..."
              disabled={!isConnected || isProcessing}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={!isConnected || isProcessing || !inputValue.trim()}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const isTool = message.role === 'tool';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[70%] rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : isTool
            ? 'bg-amber-50 text-amber-900 border border-amber-200'
            : 'bg-white text-gray-900 border border-gray-200'
        }`}
      >
        <div className="prose prose-sm max-w-none dark:prose-invert">
          {isUser ? (
            <p className="text-white m-0">{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Custom styling for code blocks
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const isInline = !match;
                  
                  return isInline ? (
                    <code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                      {children}
                    </code>
                  ) : (
                    <code className={`${className} block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto`} {...props}>
                      {children}
                    </code>
                  );
                },
                // Custom styling for links
                a({ node, children, ...props }) {
                  return (
                    <a className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer" {...props}>
                      {children}
                    </a>
                  );
                },
                // Custom styling for lists
                ul({ node, children, ...props }) {
                  return <ul className="list-disc pl-4 my-2" {...props}>{children}</ul>;
                },
                ol({ node, children, ...props }) {
                  return <ol className="list-decimal pl-4 my-2" {...props}>{children}</ol>;
                },
                // Custom styling for headings
                h1({ node, children, ...props }) {
                  return <h1 className="text-2xl font-bold mt-4 mb-2" {...props}>{children}</h1>;
                },
                h2({ node, children, ...props }) {
                  return <h2 className="text-xl font-bold mt-3 mb-2" {...props}>{children}</h2>;
                },
                h3({ node, children, ...props }) {
                  return <h3 className="text-lg font-bold mt-2 mb-1" {...props}>{children}</h3>;
                },
                // Custom styling for paragraphs
                p({ node, children, ...props }) {
                  return <p className="my-2" {...props}>{children}</p>;
                },
                // Custom styling for blockquotes
                blockquote({ node, children, ...props }) {
                  return (
                    <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2" {...props}>
                      {children}
                    </blockquote>
                  );
                },
                // Custom styling for tables
                table({ node, children, ...props }) {
                  return (
                    <div className="overflow-x-auto my-4">
                      <table className="min-w-full border-collapse border border-gray-300" {...props}>
                        {children}
                      </table>
                    </div>
                  );
                },
                th({ node, children, ...props }) {
                  return <th className="border border-gray-300 bg-gray-100 px-4 py-2 font-bold" {...props}>{children}</th>;
                },
                td({ node, children, ...props }) {
                  return <td className="border border-gray-300 px-4 py-2" {...props}>{children}</td>;
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
          {message.isStreaming && (
            <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
          )}
        </div>
        <div className={`text-xs mt-2 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
