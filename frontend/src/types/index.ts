export type Restaurant = {
    name: string;
    categories: string[];
    categorySet: number[];
    address: string;
    position?: {
      lat: number;
      lon: number;
    };
  };
  
  export type LocationData = {
    name: string;
    latitude: number;
    longitude: number;
  };
  
  export type SearchData = {
    location: LocationData | null;
    restaurants: (Restaurant | null)[];
  };