import { Restaurant, LocationData, SearchData } from '@/types';

class AppStore {
  private data: SearchData = {
    location: null,
    restaurants: Array(5).fill(null)
  };

  private currentSearchId: number | null = null;
  private listeners: (() => void)[] = [];

  getLocation(): LocationData | null {
    console.log('Getting location from store:', this.data.location);
    return this.data.location;
  }

  setLocation(location: LocationData | null): void {
    console.log('Setting location in store:', location);
    this.data.location = location;
    this.notifyListeners();
  }

  getRestaurants(): (Restaurant | null)[] {
    console.log('Getting restaurants from store:', this.data.restaurants);
    return [...this.data.restaurants];
  }

  setRestaurants(restaurants: (Restaurant | null)[]): void {
    console.log('Setting restaurants in store:', restaurants);
    this.data.restaurants = [...restaurants];
    this.notifyListeners();
  }

  updateRestaurant(index: number, restaurant: Restaurant): void {
    console.log(`Updating restaurant at index ${index}:`, restaurant);
    this.data.restaurants[index] = restaurant;
    this.notifyListeners();
  }

  getAllData(): SearchData {
    return {
      location: this.data.location,
      restaurants: [...this.data.restaurants]
    };
  }

  setCurrentSearchId(searchId: number): void {
    console.log('Setting current search ID:', searchId);
    this.currentSearchId = searchId;
    this.notifyListeners();
  }

  getCurrentSearchId(): number | null {
    return this.currentSearchId;
  }

  clearData(): void {
    console.log('Clearing all store data');
    this.data = {
      location: null,
      restaurants: Array(5).fill(null)
    };
    this.currentSearchId = null;
    this.notifyListeners();
  }

  subscribe(listener: () => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener());
  }
}

export const store = new AppStore();