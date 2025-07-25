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
  Settings
} from "lucide-react";

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
}

interface Chat {
  id: string;
  title: string;
  messages: Message[];
  lastUpdated: Date;
}

const Dashboard = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const currentChat = chats.find(chat => chat.id === currentChatId);

  useEffect(() => {
    const isAuthenticated = localStorage.getItem("isAuthenticated");
    if (!isAuthenticated) {
      navigate("/");
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    toast({
      title: "Logged out",
      description: "See you next time!",
    });
    navigate("/");
  };

  const createNewChat = () => {
    const newChat: Chat = {
      id: Date.now().toString(),
      title: "New Chat",
      messages: [],
      lastUpdated: new Date()
    };
    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
  };

  const deleteChat = (chatId: string) => {
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    if (currentChatId === chatId) {
      setCurrentChatId(null);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !currentChatId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: newMessage.trim(),
      role: "user",
      timestamp: new Date()
    };

    // Add user message
    setChats(prev => prev.map(chat => 
      chat.id === currentChatId 
        ? { 
            ...chat, 
            messages: [...chat.messages, userMessage],
            title: chat.messages.length === 0 ? newMessage.slice(0, 30) + "..." : chat.title,
            lastUpdated: new Date()
          }
        : chat
    ));

    setNewMessage("");
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: generateAIResponse(newMessage),
        role: "assistant",
        timestamp: new Date()
      };

      setChats(prev => prev.map(chat => 
        chat.id === currentChatId 
          ? { 
              ...chat, 
              messages: [...chat.messages, aiResponse],
              lastUpdated: new Date()
            }
          : chat
      ));
      setIsTyping(false);
    }, 1500);
  };

  const generateAIResponse = (userInput: string): string => {
    const lowerInput = userInput.toLowerCase();
    
    if (lowerInput.includes("dress") || lowerInput.includes("clothing")) {
      return "I'd be happy to help you with our dress collection! We have a wide range of styles from casual to formal wear. What type of dress are you looking for? Evening wear, casual, business attire, or something for a special occasion?";
    }
    
    if (lowerInput.includes("size") || lowerInput.includes("fit")) {
      return "For sizing, we offer sizes XS to 3XL for most of our dresses. I recommend checking our size guide for accurate measurements. Would you like me to help you find the perfect fit for a specific style?";
    }
    
    if (lowerInput.includes("price") || lowerInput.includes("cost")) {
      return "Our dress prices range from $49 for casual styles to $299 for premium evening wear. We frequently have sales and promotions. Would you like to know about current deals or a specific price range?";
    }
    
    if (lowerInput.includes("return") || lowerInput.includes("exchange")) {
      return "We offer a 30-day return policy for unworn items with tags attached. Exchanges are free within this period. Refunds are processed within 5-7 business days. Do you need help with a specific return?";
    }
    
    return "Thank you for your inquiry! As your fashion sales assistant, I'm here to help you find the perfect dress from our collection. Feel free to ask about styles, sizes, prices, or any other questions about our products.";
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <div className="w-80 bg-card border-r border-border flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <h1 className="text-lg font-semibold">ChicChat Admin</h1>
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

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentChat ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-border bg-card/50">
              <h2 className="text-lg font-semibold">{currentChat.title}</h2>
              <p className="text-sm text-muted-foreground">
                Fashion Sales Assistant
              </p>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="max-w-3xl mx-auto space-y-4">
                {currentChat.messages.length === 0 && (
                  <div className="text-center py-12">
                    <Sparkles className="h-12 w-12 mx-auto mb-4 text-primary" />
                    <h3 className="text-lg font-semibold mb-2">Start a conversation</h3>
                    <p className="text-muted-foreground">
                      Ask me anything about our dress collection!
                    </p>
                  </div>
                )}
                
                {currentChat.messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg transition-smooth ${
                        message.role === "user"
                          ? "bg-chat-bubble-user text-primary-foreground ml-auto"
                          : "bg-chat-bubble-assistant text-foreground"
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString()}
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
            <div className="p-4 border-t border-border bg-card/50">
              <div className="max-w-3xl mx-auto flex gap-2">
                <Input
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 transition-smooth focus:ring-2 focus:ring-primary/20"
                  disabled={isTyping}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!newMessage.trim() || isTyping}
                  className="bg-gradient-primary hover:opacity-90 transition-smooth shadow-soft"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </>
        ) : (
          // Welcome Screen
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="p-6 rounded-full bg-gradient-primary/10 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
              <h2 className="text-2xl font-bold mb-4 bg-gradient-primary bg-clip-text text-transparent">
                Welcome to ChicChat Admin
              </h2>
              <p className="text-muted-foreground mb-6 max-w-md">
                Your intelligent fashion sales assistant. Create a new chat to start helping customers find their perfect dress.
              </p>
              <Button 
                onClick={createNewChat}
                className="bg-gradient-primary hover:opacity-90 transition-smooth shadow-soft"
              >
                <Plus className="h-4 w-4 mr-2" />
                Start New Chat
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;