import { BrowserRouter, Routes, Route } from "react-router-dom";
import GlobalHeader from "./components/global-header";
import HomePage from "./pages/home";
import NotFound from "./pages/not-found";

export default function App() {
  const Router = BrowserRouter;

  return (
    <Router>
      <GlobalHeader />

      <Routes>
        <Route index path="/" element={<HomePage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}
