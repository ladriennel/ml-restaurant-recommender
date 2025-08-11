export type Restaurant = {
    name: string;
    categories: string[];
    categorySet: number[];
    address: string;
    position?: {
      lat: number;
      lon: number;
    };
    tomtom_poi_id?: string;
  };

  export type CityRestaurant = {
    name: string;
    categories: string[];
    categorySet: number[];
    address: string;
    position?: {
      lat: number;
      lon: number;
    };
    tomtom_poi_id?: string;
  };
  
  export type LocationData = {
    name: string;
    latitude: number;
    longitude: number;
    population: number;
  };
  
  export type SearchData = {
    location: LocationData | null;
    restaurants: (Restaurant | null)[];
  };

  export type RecommendationResult = {
    restaurant_id: number;
    restaurant_name: string;
    address: string;
    tomtom_poi_id: string;
    similarity_score: number;
    feature_scores: {
      cuisine: number;
      price: number;
      description: number;
      review: number;
      menu: number;
      tags: number;
    };
    explanation: string;
  };

  export type RecommendationRequest = {
    search_id: number;
    top_k?: number;
  };