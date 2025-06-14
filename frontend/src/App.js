import { useState } from "react";
import { Dialog } from "@headlessui/react";
import Button from "./components/ui/Button";
import SearchBar from "./components/ui/SearchBar";


export default function HomePage() {
  const [isOpen, setIsOpen] = useState(false);

  const handleSearch = (query) => {
    console.log("User searched for:", query);
    // 🔗 Insert your API call here
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="text-4xl font-bold mb-4">Foreclosed</h1>
        <p className="text-lg text-gray-600 mb-8">
          Search for foreclosed properties in your area. Find your next investment opportunity with ease.
        </p>

        {/* 🔍 SearchBar goes here */}
        <div className="mb-6">
          <SearchBar onSearch={handleSearch} />
        </div>

        
      </div>

      
    </main>
  );
}
