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
    distance_from_center?: number;
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