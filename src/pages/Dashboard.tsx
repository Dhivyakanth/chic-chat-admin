import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useToast } from "@/hooks/use-toast";
import { 
  Send, 
  LogOut, 
  Sparkles, 
  MessageCircle, 
  Plus,
  Trash2,
  AlertCircle,
  Wifi,
  WifiOff
} from "lucide-react";
import { chatbotApi, checkBackendConnection, type Chat as ApiChat, type Message as ApiMessage } from "@/lib/chatbot-api";
import { Alert, AlertDescription } from "@/components/ui/alert";

const Dashboard = () => {
  const [chats, setChats] = useState<ApiChat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [isCheckingConnection, setIsCheckingConnection] = useState(true);
  const navigate = useNavigate();
  const { toast } = useToast();

  const currentChat = chats.find(chat => chat.id === currentChatId);

  // Check backend connection on component mount
  useEffect(() => {
    const checkConnection = async () => {
      setIsCheckingConnection(true);
      const connected = await checkBackendConnection();
      setIsBackendConnected(connected);
      setIsCheckingConnection(false);
      
      if (!connected) {
        toast({
          title: "Backend Connection Failed",
          description: "Please make sure the Python backend server is running on port 8000",
          variant: "destructive",
        });
      } else {
        // Load existing chats if connected
        loadChats();
      }
    };
    
    checkConnection();
  }, [toast]);

  useEffect(() => {
    const isAuthenticated = localStorage.getItem("isAuthenticated");
    if (!isAuthenticated) {
      navigate("/");
    }
  }, [navigate]);

  const loadChats = async () => {
    try {
      const response = await chatbotApi.getAllChats();
      if (response.success && response.data) {
        setChats(response.data);
      }
    } catch (error) {
      console.error("Failed to load chats:", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    toast({
      title: "Logged out",
      description: "See you next time!",
    });
    navigate("/");
  };

  const createNewChat = async () => {
    if (!isBackendConnected) {
      toast({
        title: "Backend Not Connected",
        description: "Please check your backend connection",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await chatbotApi.createNewChat();
      if (response.success && response.data) {
        setChats(prev => [response.data!, ...prev]);
        setCurrentChatId(response.data!.id);
        toast({
          title: "New Chat Created",
          description: "You can start asking questions about sales data!",
        });
      } else {
        throw new Error(response.error || "Failed to create chat");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create new chat",
        variant: "destructive",
      });
    }
  };

  const deleteChat = async (chatId: string) => {
    try {
      const response = await chatbotApi.deleteChat(chatId);
      if (response.success) {
        setChats(prev => prev.filter(chat => chat.id !== chatId));
        if (currentChatId === chatId) {
          setCurrentChatId(null);
        }
        toast({
          title: "Chat Deleted",
          description: "Chat has been successfully deleted",
        });
      } else {
        throw new Error(response.error || "Failed to delete chat");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to delete chat",
        variant: "destructive",
      });
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !currentChatId || !isBackendConnected) return;

    const messageText = newMessage.trim();
    setNewMessage("");
    setIsTyping(true);

    try {
      const response = await chatbotApi.sendMessage(currentChatId, messageText);
      
      if (response.success && response.data) {
        // Update the chat with new messages
        setChats(prev => prev.map(chat => 
          chat.id === currentChatId ? response.data!.chat : chat
        ));
        
        toast({
          title: "Response Generated",
          description: "Your sales data analysis is ready!",
        });
      } else {
        throw new Error(response.error || "Failed to send message");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message",
        variant: "destructive",
      });
      
      // Re-add the message to input if it failed
      setNewMessage(messageText);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: any) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (isCheckingConnection) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Sparkles className="h-8 w-8 mx-auto mb-4 text-primary animate-pulse" />
          <p className="text-muted-foreground">Connecting to backend...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row">
      {/* Backend Connection Status */}
      {!isBackendConnected && (
        <div className="p-4 bg-destructive/10 border-b border-destructive/20">
          <Alert className="border-destructive/20 bg-destructive/10">
            <WifiOff className="h-4 w-4" />
            <AlertDescription>
              Backend server not connected. Please run: <code className="font-mono">python flask_server.py</code>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Mobile Header */}
      <div className="md:hidden p-4 border-b border-border bg-card flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold">Sales Chatbot</h1>
          {isBackendConnected ? (
            <Wifi className="h-4 w-4 text-green-500" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-500" />
          )}
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="text-muted-foreground hover:text-foreground"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Sidebar - Hidden on mobile, shown on desktop */}
      <div className="hidden md:flex w-80 bg-card border-r border-border flex-col">
        {/* Desktop Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <h1 className="text-lg font-semibold">Sales Chatbot</h1>
              {isBackendConnected ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-500" />
              )}
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="text-muted-foreground hover:text-foreground"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          <Button 
            onClick={createNewChat}
            disabled={!isBackendConnected}
            className="w-full bg-gradient-primary hover:opacity-90 transition-smooth"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Chat
          </Button>
        </div>

        {/* Chat List */}
        <ScrollArea className="flex-1 p-2">
          {chats.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              <MessageCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No chats yet</p>
            </div>
          ) : (
            <div className="space-y-1">
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className={`group p-3 rounded-lg cursor-pointer transition-smooth hover:bg-accent ${
                    currentChatId === chat.id ? "bg-accent" : ""
                  }`}
                  onClick={() => setCurrentChatId(chat.id)}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium truncate flex-1">
                      {chat.title}
                    </h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="opacity-0 group-hover:opacity-100 transition-smooth h-6 w-6 p-0"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(chat.id);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {chat.messages.length} messages
                  </p>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Mobile New Chat Button */}
      <div className="md:hidden p-4 border-b border-border bg-card">
        <Button 
          onClick={createNewChat}
          disabled={!isBackendConnected}
          className="w-full bg-gradient-primary hover:opacity-90 transition-smooth"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Mobile Chat List - Collapsible */}
      {chats.length > 0 && (
        <div className="md:hidden">
          <ScrollArea className="max-h-32 border-b border-border bg-card">
            <div className="p-2 space-y-1">
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className={`group p-2 rounded-lg cursor-pointer transition-smooth hover:bg-accent flex items-center justify-between ${
                    currentChatId === chat.id ? "bg-accent" : ""
                  }`}
                  onClick={() => setCurrentChatId(chat.id)}
                >
                  <h3 className="text-sm font-medium truncate flex-1">
                    {chat.title}
                  </h3>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-muted-foreground">
                      {chat.messages.length}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(chat.id);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {currentChat ? (
          <>
            {/* Chat Header - Hidden on mobile to save space */}
            <div className="hidden md:block p-4 border-b border-border bg-card/50">
              <h2 className="text-lg font-semibold">{currentChat.title}</h2>
              <p className="text-sm text-muted-foreground">
                AI-Powered Sales Data Analytics
              </p>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-2 md:p-4">
              <div className="max-w-3xl mx-auto space-y-4">
                {currentChat.messages.length === 0 && (
                  <div className="text-center py-8 md:py-12">
                    <Sparkles className="h-8 w-8 md:h-12 md:w-12 mx-auto mb-4 text-primary" />
                    <h3 className="text-base md:text-lg font-semibold mb-2">Start analyzing your sales data</h3>
                    <p className="text-sm md:text-base text-muted-foreground px-4">
                      Ask me about sales trends, predictions, customer insights, and more!
                    </p>
                  </div>
                )}
                
                {currentChat.messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] md:max-w-xs lg:max-w-md px-3 py-2 md:px-4 md:py-2 rounded-lg transition-smooth ${
                        message.role === "user"
                          ? "bg-chat-bubble-user text-primary-foreground ml-auto"
                          : "bg-chat-bubble-assistant text-foreground"
                      }`}
                    >
                      <div className="text-sm leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </div>
                      <p className="text-xs opacity-70 mt-1">
                        {formatTimestamp(message.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-chat-bubble-assistant text-foreground px-4 py-2 rounded-lg">
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Message Input */}
            <div className="p-2 md:p-4 border-t border-border bg-card/50">
              <div className="max-w-3xl mx-auto flex gap-2">
                <Input
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={isBackendConnected ? "Ask about sales data, trends, predictions..." : "Backend not connected"}
                  className="flex-1 transition-smooth focus:ring-2 focus:ring-primary/20 text-sm md:text-base"
                  disabled={isTyping || !isBackendConnected}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!newMessage.trim() || isTyping || !isBackendConnected}
                  className="bg-gradient-primary hover:opacity-90 transition-smooth shadow-soft h-10 w-10 md:h-auto md:w-auto md:px-4"
                >
                  <Send className="h-4 w-4" />
                  <span className="hidden md:inline ml-2">Send</span>
                </Button>
              </div>
            </div>
          </>
        ) : (
          // Welcome Screen
          <div className="flex-1 flex items-center justify-center p-4">
            <div className="text-center">
              <div className="p-4 md:p-6 rounded-full bg-gradient-primary/10 w-16 h-16 md:w-24 md:h-24 mx-auto mb-4 md:mb-6 flex items-center justify-center">
                <Sparkles className="h-8 w-8 md:h-12 md:w-12 text-primary" />
              </div>
              <h2 className="text-xl md:text-2xl font-bold mb-4 bg-gradient-primary bg-clip-text text-transparent">
                Welcome to Sales Analytics AI
              </h2>
              <p className="text-sm md:text-base text-muted-foreground mb-6 max-w-md mx-auto px-4">
                Your intelligent sales data analysis assistant. Create a new chat to start exploring your fashion sales insights, trends, and predictions.
              </p>
              {isBackendConnected ? (
                <Button 
                  onClick={createNewChat}
                  className="bg-gradient-primary hover:opacity-90 transition-smooth shadow-soft w-full md:w-auto"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Start New Analysis
                </Button>
              ) : (
                <Alert className="max-w-md mx-auto">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Please start the backend server to begin analysis
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
