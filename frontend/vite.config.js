import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
	plugins: [react()],
	server: {
		host: true,
		port: 5173,
		allowedHosts: ['localhost:5173', '10.66.66.3:5173', 'http://109.196.102.221'],
	},
});
