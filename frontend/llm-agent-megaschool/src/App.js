import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  createTheme,
  ThemeProvider
} from '@mui/material';
import { API_BASE_URL } from "./config";

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [requestId, setRequestId] = useState(1);

  const darkTheme = createTheme({
    palette: {
      mode: 'dark',
      primary: { main: '#1976d2' },
      secondary: { main: '#9c27b0' }
    },
    typography: { fontFamily: 'Roboto, Arial, sans-serif' }
  });

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const userMessage = { sender: 'user', text: inputValue };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: inputValue, id: requestId })
      });
      setRequestId(prev => prev + 1);
      if (!response.ok) {
        throw new Error(`Request error: ${response.status}`);
      }
      const data = await response.json();

      // Разделяем ответ бота на несколько сообщений
      const botMessages = [
        {
          sender: 'bot',
          text: `answer: ${data.answer === null ? 'null' : data.answer}`
        },
        {
          sender: 'bot',
          text: `reasoning: ${data.reasoning}`
        },
        {
          sender: 'bot',
          text: data.sources && data.sources.length > 0
            ? `sources: ${data.sources.join(', ')}`
            : 'sources: (нет ссылок)'
        }
      ];

      setMessages(prev => [...prev, ...botMessages]);
    } catch (error) {
      const errorMessage = { sender: 'bot', text: `Error: ${error.message}` };
      setMessages(prev => [...prev, errorMessage]);
    }
    setInputValue('');
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <Container maxWidth="sm" sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ textAlign: 'center' }}>
          ITMO Chat Demo
        </Typography>
        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Box
              sx={{
                border: '1px solid',
                borderColor: 'grey.700',
                height: 300,
                overflowY: 'auto',
                padding: 2,
                mb: 2,
                borderRadius: 1
              }}
            >
              {messages.map((msg, idx) => (
                <Box key={idx} sx={{ mb: 1 }}>
                  <Typography variant="subtitle2" component="span" sx={{ fontWeight: 'bold' }}>
                    {msg.sender}:
                  </Typography>{' '}
                  <Typography variant="body2" component="span">
                    {msg.text}
                  </Typography>
                </Box>
              ))}
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                label="Type your message"
                variant="outlined"
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
              />
              <Button
                variant="contained"
                color="primary"
                onClick={handleSend}
                sx={{ whiteSpace: 'nowrap' }}
              >
                Send
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </ThemeProvider>
  );
}

export default App;
