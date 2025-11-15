// WebSocket hook for AG UI Protocol

import { useEffect, useRef, useState, useCallback } from 'react';
import { AgentEvent, EventType, Message } from '@/lib/ag-ui-protocol';

export function useAgentWebSocket(url: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messageBufferRef = useRef<Map<string, string>>(new Map());

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const agEvent: AgentEvent = JSON.parse(event.data);
        handleAgentEvent(agEvent);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      // Reconnect after 3 seconds
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          window.location.reload();
        }
      }, 3000);
    };

    return () => {
      ws.close();
    };
  }, [url]);

  const handleAgentEvent = useCallback((event: AgentEvent) => {
    console.log('AG UI Event:', event);

    switch (event.type) {
      case EventType.RUN_STARTED:
        setIsProcessing(true);
        break;

      case EventType.TEXT_MESSAGE_START:
        // Create a new message placeholder
        messageBufferRef.current.set(event.message_id, '');
        setMessages((prev) => [
          ...prev,
          {
            id: event.message_id,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isStreaming: true,
          },
        ]);
        break;

      case EventType.TEXT_MESSAGE_CONTENT:
        // Append content to buffer
        const currentContent = messageBufferRef.current.get(event.message_id) || '';
        messageBufferRef.current.set(event.message_id, currentContent + event.delta);
        
        // Update message in state
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === event.message_id
              ? { ...msg, content: currentContent + event.delta }
              : msg
          )
        );
        break;

      case EventType.TEXT_MESSAGE_END:
        // Finalize message
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === event.message_id
              ? { ...msg, isStreaming: false }
              : msg
          )
        );
        messageBufferRef.current.delete(event.message_id);
        break;

      case EventType.TOOL_CALL_START:
        setMessages((prev) => [
          ...prev,
          {
            id: event.tool_call_id,
            role: 'tool',
            content: `🔧 Calling tool: ${event.tool_call_name}`,
            timestamp: new Date(),
          },
        ]);
        break;

      case EventType.TOOL_CALL_RESULT:
        setMessages((prev) => [
          ...prev,
          {
            id: event.tool_call_id + '-result',
            role: 'tool',
            content: `📊 ${event.content}`,
            timestamp: new Date(),
          },
        ]);
        break;

      case EventType.RUN_FINISHED:
        setIsProcessing(false);
        break;

      case EventType.RUN_ERROR:
        setIsProcessing(false);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: `❌ Error: ${event.message}`,
            timestamp: new Date(),
          },
        ]);
        break;
    }
  }, []);

  const sendMessage = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.error('WebSocket is not connected');
        return;
      }

      // Add user message to UI
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send to server
      wsRef.current.send(JSON.stringify({ message: content }));
    },
    []
  );

  return {
    messages,
    isConnected,
    isProcessing,
    sendMessage,
  };
}
