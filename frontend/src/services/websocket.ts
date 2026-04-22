export interface ConversationMessage {
  from: 'user' | 'obj';
  text: string;
  timestamp?: number;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: ((message: ConversationMessage) => void)[] = [];
  private statusHandlers: ((status: string) => void)[] = [];

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.notifyStatus('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'response') {
              const message: ConversationMessage = {
                from: 'obj',
                text: data.text,
                timestamp: Date.now(),
              };
              this.notifyMessage(message);
            } else if (data.type === 'status') {
              this.notifyStatus(data.status);
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.notifyStatus('error');
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket closed');
          this.notifyStatus('disconnected');
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.notifyStatus('failed');
    }
  }

  sendMessage(text: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'message',
        text,
      }));
    } else {
      console.error('WebSocket is not connected');
      throw new Error('WebSocket is not connected');
    }
  }

  sendAudio(audioBlob: Blob) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      audioBlob.arrayBuffer().then(buffer => {
        this.ws?.send(buffer);
      });
    } else {
      console.error('WebSocket is not connected');
      throw new Error('WebSocket is not connected');
    }
  }

  onMessage(handler: (message: ConversationMessage) => void) {
    this.messageHandlers.push(handler);
  }

  onStatus(handler: (status: string) => void) {
    this.statusHandlers.push(handler);
  }

  private notifyMessage(message: ConversationMessage) {
    this.messageHandlers.forEach(handler => handler(message));
  }

  private notifyStatus(status: string) {
    this.statusHandlers.forEach(handler => handler(status));
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}
